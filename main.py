from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
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
        if filename.startswith(file_id) and not filename.endswith(('.meta', '.tempconfig')):
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

        if os.path.exists(temp_config_path):
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
        else:
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
    temp_config: Optional[str] = Form(None)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)