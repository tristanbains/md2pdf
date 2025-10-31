from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import io
from pdf_generator import PDFGenerator
from typing import Optional
import yaml
import json
import uuid
import os
from datetime import datetime, timedelta

app = FastAPI(title="Markdown to PDF Converter")

templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "temp_uploads"

def cleanup_old_files():
    """Remove all files from temp_uploads to keep only the most recent upload"""
    if not os.path.exists(UPLOAD_DIR):
        return

    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

def save_uploaded_file(content: bytes, original_filename: str) -> str:
    """Save uploaded file and return unique file_id"""
    cleanup_old_files()
    
    file_id = str(uuid.uuid4())
    file_extension = Path(original_filename).suffix
    stored_filename = f"{file_id}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)
    metadata_path = os.path.join(UPLOAD_DIR, f"{file_id}.meta")
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(file_path, 'wb') as f:
        f.write(content)

    with open(metadata_path, 'w') as f:
        f.write(original_filename)
    
    return file_id

def get_file_content(file_id: str) -> tuple[str, str]:
    """Get file content and original filename by file_id"""
    metadata_path = os.path.join(UPLOAD_DIR, f"{file_id}.meta")
    original_filename = None

    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            original_filename = f.read().strip()

    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(file_id) and not filename.endswith(('.meta', '.tempconfig', '.preset')):
            file_path = os.path.join(UPLOAD_DIR, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            display_filename = original_filename if original_filename else filename
            return content, display_filename

    raise FileNotFoundError(f"File with ID {file_id} not found")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    pdf_gen = PDFGenerator()
    available_themes = pdf_gen.get_available_themes()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "config": pdf_gen.config,
            "available_themes": available_themes
        }
    )

@app.get("/api/config")
async def get_config():
    pdf_gen = PDFGenerator()
    return pdf_gen.config

@app.get("/api/config/factory-reset")
async def get_factory_config():
    """Return factory default configuration"""
    full_config = PDFGenerator.get_default_config()
    return {
        'prose_size': full_config['prose_size'],
        'prose_color': full_config['prose_color'],
        'codehilite_theme': full_config['codehilite_theme'],
        'codehilite_container': full_config['codehilite_container'],
        'custom_classes': full_config['custom_classes']
    }

@app.post("/api/config")
async def update_config(
    prose_size: str = Form(...),
    prose_color: str = Form(""),
    codehilite_theme: str = Form("default"),
    codehilite_auto_bg: bool = Form(True),
    codehilite_custom_bg: str = Form(""),
    codehilite_wrapper_classes: str = Form(""),
    h1_classes: str = Form(""),
    h2_classes: str = Form(""),
    h3_classes: str = Form(""),
    h4_classes: str = Form(""),
    h5_classes: str = Form(""),
    h6_classes: str = Form(""),
    p_classes: str = Form(""),
    a_classes: str = Form(""),
    code_classes: str = Form(""),
    pre_classes: str = Form(""),
    blockquote_classes: str = Form(""),
    table_classes: str = Form(""),
    thead_classes: str = Form(""),
    tbody_classes: str = Form(""),
    tr_classes: str = Form(""),
    td_classes: str = Form(""),
    th_classes: str = Form(""),
    ul_classes: str = Form(""),
    ol_classes: str = Form(""),
    li_classes: str = Form(""),
    img_classes: str = Form(""),
    hr_classes: str = Form("")
):
    updates = {
        "prose_size": prose_size,
        "prose_color": prose_color,
        "codehilite_theme": codehilite_theme,
        "codehilite_container": {
            "auto_background": codehilite_auto_bg,
            "custom_background": codehilite_custom_bg,
            "wrapper_classes": codehilite_wrapper_classes
        },
        "custom_classes": {
            "h1": h1_classes,
            "h2": h2_classes,
            "h3": h3_classes,
            "h4": h4_classes,
            "h5": h5_classes,
            "h6": h6_classes,
            "p": p_classes,
            "a": a_classes,
            "code": code_classes,
            "pre": pre_classes,
            "blockquote": blockquote_classes,
            "table": table_classes,
            "thead": thead_classes,
            "tbody": tbody_classes,
            "tr": tr_classes,
            "td": td_classes,
            "th": th_classes,
            "ul": ul_classes,
            "ol": ol_classes,
            "li": li_classes,
            "img": img_classes,
            "hr": hr_classes
        }
    }

    pdf_gen = PDFGenerator()
    pdf_gen.update_config(updates)
    return {"status": "success", "message": "Configuration updated"}

@app.get("/preview/{file_id}", response_class=HTMLResponse)
async def preview_markdown(request: Request, file_id: str):
    """Serve styled HTML preview of markdown file"""
    try:
        markdown_content, filename = get_file_content(file_id)

        # Check for temporary config first
        temp_config_path = os.path.join(UPLOAD_DIR, f"{file_id}.tempconfig")
        preset_marker_path = os.path.join(UPLOAD_DIR, f"{file_id}.preset")

        if os.path.exists(temp_config_path):
            # Use temporary config (from "Generate Without Saving")
            try:
                with open(temp_config_path, 'r') as f:
                    temp_config = json.load(f)

                if not isinstance(temp_config, dict) or 'custom_classes' not in temp_config:
                    pdf_gen = PDFGenerator()
                else:
                    pdf_gen = PDFGenerator()
                    pdf_gen.config = temp_config
            except Exception as e:
                pdf_gen = PDFGenerator()
        elif os.path.exists(preset_marker_path):
            # Use preset config (from preset selection + upload)
            try:
                with open(preset_marker_path, 'r') as f:
                    preset_slug = f.read().strip()

                # Load preset config
                pdf_gen = PDFGenerator()
                preset_path = pdf_gen.factory_presets_dir / f"{preset_slug}.yaml"
                if not preset_path.exists():
                    preset_path = pdf_gen.user_presets_dir / f"{preset_slug}.yaml"

                if preset_path.exists():
                    with open(preset_path, 'r') as f:
                        preset_data = yaml.safe_load(f)
                    # Remove metadata and apply preset config
                    preset_data.pop('_metadata', None)
                    pdf_gen.config = preset_data
            except Exception as e:
                print(f"Error loading preset from marker: {e}")
                pdf_gen = PDFGenerator()
        else:
            # Use backend config.yaml (from saved settings or loaded preset)
            pdf_gen = PDFGenerator()

        try:
            html_body = pdf_gen.markdown_to_html(markdown_content)
            html_body = pdf_gen.apply_custom_classes(html_body)
            html_body = pdf_gen.apply_codehilite_wrapper_styling(html_body)
        except Exception as e:
            html_body = pdf_gen.markdown_to_html(markdown_content)

        original_filename = Path(filename).stem
        codehilite_css = pdf_gen.get_codehilite_css()

        return templates.TemplateResponse(
            "preview.html",
            {
                "request": request,
                "html_content": html_body,
                "filename": original_filename,
                "config": pdf_gen.config,
                "codehilite_css": codehilite_css
            }
        )
    except FileNotFoundError:
        return HTMLResponse("<h1>File not found</h1><p>The requested file may have expired or does not exist.</p>", status_code=404)
    except Exception as e:
        return HTMLResponse(f"<h1>Error</h1><p>Failed to load preview: {str(e)}</p>", status_code=500)

@app.get("/theme-preview", response_class=HTMLResponse)
async def theme_preview(request: Request, current: Optional[str] = None):
    """Display all available Pygments themes with sample code"""
    pdf_gen = PDFGenerator()

    # Get all available themes
    available_themes = pdf_gen.get_available_themes()

    # Sample Python code for preview (with syntax highlighting markup)
    sample_code = '''<span class="k">def</span> <span class="nf">fibonacci</span><span class="p">(</span><span class="n">n</span><span class="p">):</span>
    <span class="k">if</span> <span class="n">n</span> <span class="o">&lt;=</span> <span class="mi">1</span><span class="p">:</span>
        <span class="k">return</span> <span class="n">n</span>
    <span class="k">return</span> <span class="n">fibonacci</span><span class="p">(</span><span class="n">n</span><span class="o">-</span><span class="mi">1</span><span class="p">)</span> <span class="o">+</span> <span class="n">fibonacci</span><span class="p">(</span><span class="n">n</span><span class="o">-</span><span class="mi">2</span><span class="p">)</span>

<span class="nb">print</span><span class="p">(</span><span class="n">fibonacci</span><span class="p">(</span><span class="mi">10</span><span class="p">))</span>'''

    # Generate CSS for each theme with scope prefix
    themes_with_css = {}
    for theme in available_themes:
        try:
            # Create scope prefix by replacing special characters
            scope_class = f".theme-{theme.replace('.', '_').replace('-', '_')}"
            css = pdf_gen.get_codehilite_css(theme, scope_prefix=scope_class)
            themes_with_css[theme] = css
        except Exception as e:
            print(f"Error generating CSS for theme {theme}: {e}")
            continue

    return templates.TemplateResponse(
        "theme_preview.html",
        {
            "request": request,
            "themes": themes_with_css,
            "sample_code": sample_code,
            "current_theme": current
        }
    )

@app.post("/api/convert")
async def convert_markdown(
    file: UploadFile = File(...),
    temp_config: Optional[str] = Form(None),
    preset_slug: Optional[str] = Form(None)
):
    try:
        # Validate file type
        if not file.filename.endswith(('.md', '.markdown')):
            return JSONResponse(
                status_code=400,
                content={"error": "Please upload a valid Markdown file (.md or .markdown)"}
            )

        # Read and store the file
        markdown_content = await file.read()
        file_id = save_uploaded_file(markdown_content, file.filename)

        # Save temporary config if provided
        if temp_config:
            temp_config_path = os.path.join(UPLOAD_DIR, f"{file_id}.tempconfig")
            with open(temp_config_path, 'w') as f:
                f.write(temp_config)
        # If preset slug provided, save preset marker
        elif preset_slug:
            preset_marker_path = os.path.join(UPLOAD_DIR, f"{file_id}.preset")
            with open(preset_marker_path, 'w') as f:
                f.write(preset_slug)

        # Return preview URL instead of PDF
        preview_url = f"/preview/{file_id}"

        return JSONResponse(
            content={
                "status": "success",
                "message": "Markdown file processed successfully",
                "preview_url": preview_url,
                "file_id": file_id,
                "filename": file.filename
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# ========== PRESET MANAGEMENT ROUTES ==========

@app.get("/api/presets")
async def list_presets():
    """List all available presets (factory + user)"""
    try:
        pdf_gen = PDFGenerator()
        presets = pdf_gen.list_presets()
        return JSONResponse(content=presets)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to list presets: {str(e)}"}
        )

@app.post("/api/presets/save")
async def save_preset(
    name: str = Form(...),
    description: str = Form(""),
    # Add all config fields from the form
    prose_size: str = Form(...),
    prose_color: str = Form(""),
    codehilite_theme: str = Form("default"),
    codehilite_auto_bg: bool = Form(True),
    codehilite_custom_bg: str = Form(""),
    codehilite_wrapper_classes: str = Form(""),
    h1_classes: str = Form(""),
    h2_classes: str = Form(""),
    h3_classes: str = Form(""),
    h4_classes: str = Form(""),
    h5_classes: str = Form(""),
    h6_classes: str = Form(""),
    p_classes: str = Form(""),
    a_classes: str = Form(""),
    code_classes: str = Form(""),
    pre_classes: str = Form(""),
    blockquote_classes: str = Form(""),
    table_classes: str = Form(""),
    thead_classes: str = Form(""),
    tbody_classes: str = Form(""),
    tr_classes: str = Form(""),
    td_classes: str = Form(""),
    th_classes: str = Form(""),
    ul_classes: str = Form(""),
    ol_classes: str = Form(""),
    li_classes: str = Form(""),
    img_classes: str = Form(""),
    hr_classes: str = Form("")
):
    """Save current form values as a named preset"""
    try:
        pdf_gen = PDFGenerator()

        # Check if name matches a factory preset (case-insensitive)
        factory_presets = pdf_gen.list_presets()['factory']
        factory_names = [p['name'].lower() for p in factory_presets]

        if name.lower() in factory_names:
            # Find the actual factory preset name (with correct casing) for error message
            matching_preset = next(p for p in factory_presets if p['name'].lower() == name.lower())
            return JSONResponse(
                status_code=400,
                content={"error": f"Cannot use factory preset name '{matching_preset['name']}'. Please choose a different name."}
            )

        # Build config from form values
        config_to_save = {
            'prose_size': prose_size,
            'prose_color': prose_color,
            'codehilite_theme': codehilite_theme,
            'codehilite_container': {
                'auto_background': codehilite_auto_bg,
                'custom_background': codehilite_custom_bg,
                'wrapper_classes': codehilite_wrapper_classes
            },
            'custom_classes': {
                'h1': h1_classes,
                'h2': h2_classes,
                'h3': h3_classes,
                'h4': h4_classes,
                'h5': h5_classes,
                'h6': h6_classes,
                'p': p_classes,
                'a': a_classes,
                'code': code_classes,
                'pre': pre_classes,
                'blockquote': blockquote_classes,
                'table': table_classes,
                'thead': thead_classes,
                'tbody': tbody_classes,
                'tr': tr_classes,
                'td': td_classes,
                'th': th_classes,
                'ul': ul_classes,
                'ol': ol_classes,
                'li': li_classes,
                'img': img_classes,
                'hr': hr_classes
            },
            'pdf_options': pdf_gen.get_default_config()['pdf_options']  # Keep default PDF options
        }

        slug = pdf_gen.save_preset_with_config(name, description, config_to_save)

        return JSONResponse(content={
            "status": "success",
            "message": f"Preset '{name}' saved successfully",
            "preset": {
                "name": name,
                "slug": slug,
                "path": f"presets/user/{slug}.yaml"
            }
        })
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to save preset: {str(e)}"}
        )

@app.post("/api/presets/load/{slug}")
async def load_preset(slug: str):
    """Load preset config and save to backend config.yaml"""
    try:
        pdf_gen = PDFGenerator()

        # Find preset file (check factory first, then user)
        preset_path = pdf_gen.factory_presets_dir / f"{slug}.yaml"
        if not preset_path.exists():
            preset_path = pdf_gen.user_presets_dir / f"{slug}.yaml"

        if not preset_path.exists():
            raise FileNotFoundError(f"Preset '{slug}' not found")

        # Load preset and save to backend config.yaml
        with open(preset_path, 'r') as f:
            preset_data = yaml.safe_load(f)

        # Get preset name for message before removing metadata
        presets = pdf_gen.list_presets()
        preset_name = slug
        for preset in presets['factory'] + presets['user']:
            if preset['slug'] == slug:
                preset_name = preset['name']
                break

        # Remove metadata before saving
        preset_data.pop('_metadata', None)

        # Update backend config.yaml with loaded preset
        pdf_gen.config = preset_data
        pdf_gen.save_config()

        return JSONResponse(content={
            "status": "success",
            "message": f"Preset '{preset_name}' loaded",
            "config": preset_data
        })
    except FileNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to load preset: {str(e)}"}
        )

@app.delete("/api/presets/delete/{slug}")
async def delete_preset(slug: str):
    """Delete user preset (cannot delete factory)"""
    try:
        pdf_gen = PDFGenerator()

        # Check if it's a factory preset
        presets = pdf_gen.list_presets()
        for preset in presets['factory']:
            if preset['slug'] == slug:
                return JSONResponse(
                    status_code=403,
                    content={"error": "Cannot delete factory presets"}
                )

        pdf_gen.delete_preset(slug)

        return JSONResponse(content={
            "status": "success",
            "message": f"Preset '{slug}' deleted successfully"
        })
    except FileNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to delete preset: {str(e)}"}
        )

@app.get("/api/presets/export/{slug}")
async def export_preset(slug: str):
    """Export preset as downloadable YAML file"""
    try:
        pdf_gen = PDFGenerator()
        preset_path = pdf_gen.export_preset(slug)

        # Get preset name for filename
        presets = pdf_gen.list_presets()
        preset_name = slug
        for preset in presets['factory'] + presets['user']:
            if preset['slug'] == slug:
                preset_name = preset['name'].lower().replace(' ', '-')
                break

        filename = f"{preset_name}.md2pdf-preset.yaml"

        return FileResponse(
            path=str(preset_path),
            media_type="application/x-yaml",
            filename=filename
        )
    except FileNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to export preset: {str(e)}"}
        )

@app.post("/api/presets/import")
async def import_preset(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None)
):
    """Import preset from uploaded YAML file"""
    try:
        # Validate file extension
        if not file.filename.endswith(('.yaml', '.yml')):
            return JSONResponse(
                status_code=400,
                content={"error": "Please upload a valid YAML file (.yaml or .yml)"}
            )

        # Read file content
        file_content = await file.read()

        pdf_gen = PDFGenerator()
        slug = pdf_gen.import_preset(file_content, name)

        # Get imported preset name
        presets = pdf_gen.list_presets()
        imported_name = slug
        for preset in presets['user']:
            if preset['slug'] == slug:
                imported_name = preset['name']
                break

        return JSONResponse(content={
            "status": "success",
            "message": f"Preset '{imported_name}' imported successfully",
            "preset": {
                "name": imported_name,
                "slug": slug
            }
        })
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to import preset: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)