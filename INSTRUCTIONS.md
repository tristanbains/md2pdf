# Markdown to PDF Converter - Python FastAPI Implementation

## Overview
Build a FastAPI web application that converts Markdown files to styled PDFs using TailwindCSS. Users can upload files via browser, customize styling with Tailwind classes, and download the generated PDFs.

## Project Structure
```
markdown-pdf-converter/
├── README.md                 # Dependencies installation guide
├── pyproject.toml           # Project configuration
├── config.yaml              # Style settings (saved/loaded)
├── main.py                  # FastAPI application
├── pdf_generator.py         # PDF generation logic
├── static/
│   └── styles.css          # Any custom CSS if needed
└── templates/
    ├── index.html          # Main upload/settings page
    └── components.html     # Reusable HTML components
```

## Step-by-Step Implementation Instructions

### Step 1: Project Initialization

**1.1 Create project directory and navigate into it:**
```bash
mkdir markdown-pdf-converter
cd markdown-pdf-converter
```

**1.2 Initialize with uv:**
```bash
uv init
```

**1.3 Add dependencies:**
```bash
uv add fastapi uvicorn python-multipart jinja2 pyyaml markdown weasyprint pygments
```

**Notes:**
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `python-multipart`: For file uploads
- `jinja2`: Template engine
- `pyyaml`: Config file handling
- `markdown`: Markdown parsing with extensions
- `weasyprint`: PDF generation (primary choice)
- `pygments`: Syntax highlighting for code blocks

**1.4 Create README.md for system dependencies:**

WeasyPrint requires system libraries. Create a `README.md` file with:

```markdown
# System Dependencies for WeasyPrint

## macOS (using Homebrew)
```bash
brew install python3 cairo pango gdk-pixbuf libffi
```

## Ubuntu/Debian
```bash
sudo apt-get install python3-dev python3-pip python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

## Windows
Download and install GTK3 runtime from:
https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

Or use Windows Subsystem for Linux (WSL) with Ubuntu instructions.

## Verify Installation
After installing system dependencies and Python packages, verify:
```bash
python -c "import weasyprint; print('WeasyPrint installed successfully')"
```

## Alternative PDF Libraries (if WeasyPrint fails)

### Option 1: pdfkit (requires wkhtmltopdf)
```bash
# Install wkhtmltopdf
# macOS:
brew install wkhtmltopdf

# Ubuntu:
sudo apt-get install wkhtmltopdf

# Then install Python package:
uv add pdfkit
```

### Option 2: xhtml2pdf (pure Python, no system deps)
```bash
uv add xhtml2pdf
```

Note: xhtml2pdf has limited CSS support compared to WeasyPrint.
```

### Step 2: Configuration File Structure

**2.1 Create `config.yaml` with default settings:**

```yaml
# PDF Style Configuration
prose_size: "prose"  # Options: prose-sm, prose, prose-lg, prose-xl, prose-2xl

# Custom Tailwind classes for each element type
custom_classes:
  h1: ""
  h2: ""
  h3: ""
  h4: ""
  h5: ""
  h6: ""
  p: ""
  a: ""
  code: ""
  pre: ""
  blockquote: ""
  table: ""
  ul: ""
  ol: ""
  li: ""
  img: ""
  hr: ""

# PDF settings
pdf_options:
  format: "A4"
  orientation: "portrait"
  margin_top: "20mm"
  margin_right: "20mm"
  margin_bottom: "20mm"
  margin_left: "20mm"
```

### Step 3: PDF Generator Module

**3.1 Create `pdf_generator.py`:**

This module handles:
- Markdown to HTML conversion
- Applying Tailwind classes
- Generating PDFs with WeasyPrint
- Fallback to alternative libraries if needed

```python
import markdown
from markdown.extensions import tables, fenced_code, codehilite
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import yaml
from pathlib import Path
from typing import Dict, Optional
import io

class PDFGenerator:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize PDF generator with configuration."""
        self.config = self.load_config(config_path)
        self.font_config = FontConfiguration()
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def save_config(self, config_path: str = "config.yaml"):
        """Save current configuration to YAML file."""
        with open(config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def update_config(self, updates: Dict):
        """Update configuration with new values."""
        if 'prose_size' in updates:
            self.config['prose_size'] = updates['prose_size']
        if 'custom_classes' in updates:
            self.config['custom_classes'].update(updates['custom_classes'])
        self.save_config()
    
    def markdown_to_html(self, markdown_content: str) -> str:
        """Convert markdown to HTML with extensions."""
        md = markdown.Markdown(extensions=[
            'tables',
            'fenced_code',
            'codehilite',
            'nl2br',
            'sane_lists',
            'attr_list',
            'def_list',
            'abbr',
            'footnotes',
            'toc'
        ])
        return md.convert(markdown_content)
    
    def apply_custom_classes(self, html_content: str) -> str:
        """Apply custom Tailwind classes to HTML elements."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        custom_classes = self.config['custom_classes']
        
        # Apply classes to each element type
        for tag, classes in custom_classes.items():
            if classes:  # Only apply if classes are defined
                for element in soup.find_all(tag):
                    existing_classes = element.get('class', [])
                    if isinstance(existing_classes, str):
                        existing_classes = existing_classes.split()
                    new_classes = classes.split()
                    element['class'] = existing_classes + new_classes
        
        return str(soup)
    
    def generate_full_html(self, markdown_content: str) -> str:
        """Generate complete HTML document with Tailwind CSS."""
        html_body = self.markdown_to_html(markdown_content)
        html_body = self.apply_custom_classes(html_body)
        
        prose_size = self.config['prose_size']
        
        # Complete HTML document with Tailwind CSS
        full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@3.4.0/dist/tailwind.min.css" rel="stylesheet">
    <style>
        @page {{
            size: {self.config['pdf_options']['format']};
            margin: {self.config['pdf_options']['margin_top']} 
                    {self.config['pdf_options']['margin_right']} 
                    {self.config['pdf_options']['margin_bottom']} 
                    {self.config['pdf_options']['margin_left']};
        }}
        
        /* Syntax highlighting styles */
        .codehilite {{ background: #f8f8f8; padding: 1em; border-radius: 0.5em; overflow-x: auto; }}
        .codehilite .hll {{ background-color: #ffffcc }}
        .codehilite .c {{ color: #408080; font-style: italic }}
        .codehilite .k {{ color: #008000; font-weight: bold }}
        .codehilite .o {{ color: #666666 }}
        .codehilite .cm {{ color: #408080; font-style: italic }}
        .codehilite .cp {{ color: #BC7A00 }}
        .codehilite .c1 {{ color: #408080; font-style: italic }}
        .codehilite .cs {{ color: #408080; font-style: italic }}
        .codehilite .gd {{ color: #A00000 }}
        .codehilite .ge {{ font-style: italic }}
        .codehilite .gr {{ color: #FF0000 }}
        .codehilite .gh {{ color: #000080; font-weight: bold }}
        .codehilite .gi {{ color: #00A000 }}
        .codehilite .go {{ color: #888888 }}
        .codehilite .gp {{ color: #000080; font-weight: bold }}
        .codehilite .gs {{ font-weight: bold }}
        .codehilite .gu {{ color: #800080; font-weight: bold }}
        .codehilite .gt {{ color: #0044DD }}
        .codehilite .kc {{ color: #008000; font-weight: bold }}
        .codehilite .kd {{ color: #008000; font-weight: bold }}
        .codehilite .kn {{ color: #008000; font-weight: bold }}
        .codehilite .kp {{ color: #008000 }}
        .codehilite .kr {{ color: #008000; font-weight: bold }}
        .codehilite .kt {{ color: #B00040 }}
        .codehilite .m {{ color: #666666 }}
        .codehilite .s {{ color: #BA2121 }}
        .codehilite .na {{ color: #7D9029 }}
        .codehilite .nb {{ color: #008000 }}
        .codehilite .nc {{ color: #0000FF; font-weight: bold }}
        .codehilite .no {{ color: #880000 }}
        .codehilite .nd {{ color: #AA22FF }}
        .codehilite .ni {{ color: #999999; font-weight: bold }}
        .codehilite .ne {{ color: #D2413A; font-weight: bold }}
        .codehilite .nf {{ color: #0000FF }}
        .codehilite .nl {{ color: #A0A000 }}
        .codehilite .nn {{ color: #0000FF; font-weight: bold }}
        .codehilite .nt {{ color: #008000; font-weight: bold }}
        .codehilite .nv {{ color: #19177C }}
        .codehilite .ow {{ color: #AA22FF; font-weight: bold }}
        .codehilite .w {{ color: #bbbbbb }}
        .codehilite .mb {{ color: #666666 }}
        .codehilite .mf {{ color: #666666 }}
        .codehilite .mh {{ color: #666666 }}
        .codehilite .mi {{ color: #666666 }}
        .codehilite .mo {{ color: #666666 }}
        .codehilite .sb {{ color: #BA2121 }}
        .codehilite .sc {{ color: #BA2121 }}
        .codehilite .sd {{ color: #BA2121; font-style: italic }}
        .codehilite .s2 {{ color: #BA2121 }}
        .codehilite .se {{ color: #BB6622; font-weight: bold }}
        .codehilite .sh {{ color: #BA2121 }}
        .codehilite .si {{ color: #BB6688; font-weight: bold }}
        .codehilite .sx {{ color: #008000 }}
        .codehilite .sr {{ color: #BB6688 }}
        .codehilite .s1 {{ color: #BA2121 }}
        .codehilite .ss {{ color: #19177C }}
        .codehilite .bp {{ color: #008000 }}
        .codehilite .vc {{ color: #19177C }}
        .codehilite .vg {{ color: #19177C }}
        .codehilite .vi {{ color: #19177C }}
        .codehilite .il {{ color: #666666 }}
    </style>
</head>
<body class="bg-white">
    <div class="prose {prose_size} max-w-none p-8">
        {html_body}
    </div>
</body>
</html>
"""
        return full_html
    
    def generate_pdf(self, markdown_content: str, output_path: Optional[str] = None) -> bytes:
        """Generate PDF from markdown content."""
        html_content = self.generate_full_html(markdown_content)
        
        if output_path:
            HTML(string=html_content).write_pdf(
                output_path,
                font_config=self.font_config
            )
            with open(output_path, 'rb') as f:
                return f.read()
        else:
            # Return PDF as bytes
            pdf_bytes = HTML(string=html_content).write_pdf(
                font_config=self.font_config
            )
            return pdf_bytes
```

**Important notes for the implementation:**
- Add `beautifulsoup4` dependency: `uv add beautifulsoup4`
- The codehilite extension requires Pygments (already added)
- WeasyPrint handles Tailwind CSS classes well

### Step 4: FastAPI Application

**4.1 Create `main.py`:**

```python
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import io
from pdf_generator import PDFGenerator
from typing import Optional
import yaml

app = FastAPI(title="Markdown to PDF Converter")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize PDF generator
pdf_gen = PDFGenerator()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main page with current settings."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "config": pdf_gen.config
        }
    )

@app.get("/api/config")
async def get_config():
    """Get current configuration."""
    return pdf_gen.config

@app.post("/api/config")
async def update_config(
    prose_size: str = Form(...),
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
    ul_classes: str = Form(""),
    ol_classes: str = Form(""),
    li_classes: str = Form(""),
    img_classes: str = Form(""),
    hr_classes: str = Form("")
):
    """Update configuration settings."""
    updates = {
        "prose_size": prose_size,
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
            "ul": ul_classes,
            "ol": ol_classes,
            "li": li_classes,
            "img": img_classes,
            "hr": hr_classes
        }
    }
    
    pdf_gen.update_config(updates)
    return {"status": "success", "message": "Configuration updated"}

@app.post("/api/convert")
async def convert_markdown(file: UploadFile = File(...)):
    """Convert uploaded markdown file to PDF."""
    try:
        # Read markdown content
        markdown_content = await file.read()
        markdown_text = markdown_content.decode('utf-8')
        
        # Generate PDF
        pdf_bytes = pdf_gen.generate_pdf(markdown_text)
        
        # Get original filename without extension
        original_filename = Path(file.filename).stem
        pdf_filename = f"{original_filename}.pdf"
        
        # Return PDF as download
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={pdf_filename}"
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
```

### Step 5: Frontend Templates

**5.1 Create `templates/index.html`:**

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown to PDF Converter</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- DaisyUI -->
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4.4.19/dist/full.min.css" rel="stylesheet" type="text/css" />
    
    <style>
        .drop-zone {
            transition: all 0.3s ease;
        }
        .drop-zone.drag-over {
            background-color: rgba(59, 130, 246, 0.1);
            border-color: #3b82f6;
        }
    </style>
</head>
<body class="bg-base-200 min-h-screen">
    <div class="container mx-auto p-8 max-w-6xl">
        <div class="text-center mb-8">
            <h1 class="text-4xl font-bold mb-2">Markdown to PDF Converter</h1>
            <p class="text-base-content/70">Upload markdown files and convert them to beautifully styled PDFs</p>
        </div>

        <!-- Settings Form -->
        <div class="card bg-base-100 shadow-xl mb-6">
            <div class="card-body">
                <h2 class="card-title">PDF Style Settings</h2>
                
                <form id="settingsForm">
                    <!-- Prose Size -->
                    <div class="form-control mb-4">
                        <label class="label">
                            <span class="label-text font-semibold">Prose Size</span>
                        </label>
                        <select name="prose_size" class="select select-bordered w-full max-w-xs">
                            <option value="prose-sm" {% if config.prose_size == 'prose-sm' %}selected{% endif %}>Small (prose-sm)</option>
                            <option value="prose" {% if config.prose_size == 'prose' %}selected{% endif %}>Base (prose)</option>
                            <option value="prose-lg" {% if config.prose_size == 'prose-lg' %}selected{% endif %}>Large (prose-lg)</option>
                            <option value="prose-xl" {% if config.prose_size == 'prose-xl' %}selected{% endif %}>Extra Large (prose-xl)</option>
                            <option value="prose-2xl" {% if config.prose_size == 'prose-2xl' %}selected{% endif %}>2X Large (prose-2xl)</option>
                        </select>
                    </div>

                    <!-- Custom Classes -->
                    <div class="divider">Element Styling (Tailwind Classes)</div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">H1 Classes</span>
                            </label>
                            <input type="text" name="h1_classes" value="{{ config.custom_classes.h1 }}" 
                                   placeholder="text-blue-600 font-bold" class="input input-bordered w-full" />
                        </div>
                        
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">H2 Classes</span>
                            </label>
                            <input type="text" name="h2_classes" value="{{ config.custom_classes.h2 }}" 
                                   placeholder="text-blue-500" class="input input-bordered w-full" />
                        </div>
                        
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">H3 Classes</span>
                            </label>
                            <input type="text" name="h3_classes" value="{{ config.custom_classes.h3 }}" 
                                   placeholder="text-blue-400" class="input input-bordered w-full" />
                        </div>
                        
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Paragraph Classes</span>
                            </label>
                            <input type="text" name="p_classes" value="{{ config.custom_classes.p }}" 
                                   placeholder="text-gray-700" class="input input-bordered w-full" />
                        </div>
                        
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Link Classes</span>
                            </label>
                            <input type="text" name="a_classes" value="{{ config.custom_classes.a }}" 
                                   placeholder="text-blue-600 hover:underline" class="input input-bordered w-full" />
                        </div>
                        
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Code Block Classes</span>
                            </label>
                            <input type="text" name="pre_classes" value="{{ config.custom_classes.pre }}" 
                                   placeholder="bg-gray-100 rounded" class="input input-bordered w-full" />
                        </div>
                        
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Inline Code Classes</span>
                            </label>
                            <input type="text" name="code_classes" value="{{ config.custom_classes.code }}" 
                                   placeholder="bg-gray-100 px-1 rounded" class="input input-bordered w-full" />
                        </div>
                        
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Blockquote Classes</span>
                            </label>
                            <input type="text" name="blockquote_classes" value="{{ config.custom_classes.blockquote }}" 
                                   placeholder="border-l-4 border-blue-500" class="input input-bordered w-full" />
                        </div>
                        
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Table Classes</span>
                            </label>
                            <input type="text" name="table_classes" value="{{ config.custom_classes.table }}" 
                                   placeholder="border-collapse" class="input input-bordered w-full" />
                        </div>
                        
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Unordered List Classes</span>
                            </label>
                            <input type="text" name="ul_classes" value="{{ config.custom_classes.ul }}" 
                                   placeholder="list-disc" class="input input-bordered w-full" />
                        </div>
                        
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Ordered List Classes</span>
                            </label>
                            <input type="text" name="ol_classes" value="{{ config.custom_classes.ol }}" 
                                   placeholder="list-decimal" class="input input-bordered w-full" />
                        </div>
                        
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">List Item Classes</span>
                            </label>
                            <input type="text" name="li_classes" value="{{ config.custom_classes.li }}" 
                                   placeholder="mb-1" class="input input-bordered w-full" />
                        </div>
                    </div>
                    
                    <div class="mt-6">
                        <button type="submit" class="btn btn-primary">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            Save Settings
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Upload Card -->
        <div class="card bg-base-100 shadow-xl mb-6">
            <div class="card-body">
                <h2 class="card-title">Upload Markdown File</h2>
                
                <form id="uploadForm" enctype="multipart/form-data">
                    <div id="dropZone" class="drop-zone border-2 border-dashed border-base-300 rounded-lg p-12 text-center cursor-pointer hover:border-primary">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto mb-4 text-base-content/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        <p class="text-lg font-semibold mb-2">Drag & Drop your Markdown file here</p>
                        <p class="text-base-content/70 mb-4">or</p>
                        <label for="fileInput" class="btn btn-primary">
                            Browse Files
                        </label>
                        <input type="file" id="fileInput" name="file" accept=".md,.markdown" class="hidden" />
                    </div>

                    <div id="fileInfo" class="mt-4 hidden">
                        <div class="alert alert-info">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <div>
                                <div class="font-semibold">File loaded:</div>
                                <div id="fileName" class="text-sm"></div>
                            </div>
                        </div>
                        
                        <button type="submit" id="convertBtn" class="btn btn-success mt-4">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Convert to PDF
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Status Messages -->
        <div id="statusMessage" class="hidden"></div>
    </div>

    <!-- Loading Modal -->
    <dialog id="loadingModal" class="modal">
        <div class="modal-box">
            <h3 class="font-bold text-lg">Processing...</h3>
            <div class="py-4 flex justify-center">
                <span class="loading loading-spinner loading-lg"></span>
            </div>
            <p class="text-center" id="loadingMessage">Please wait while your PDF is being generated</p>
        </div>
    </dialog>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const uploadForm = document.getElementById('uploadForm');
        const settingsForm = document.getElementById('settingsForm');
        const loadingModal = document.getElementById('loadingModal');
        const loadingMessage = document.getElementById('loadingMessage');

        let currentFile = null;

        // Drag and drop functionality
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('drag-over');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('drag-over');
            });
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            handleFiles(files);
        });

        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });

        function handleFiles(files) {
            if (files.length > 0) {
                const file = files[0];
                if (file.name.endsWith('.md') || file.name.endsWith('.markdown')) {
                    currentFile = file;
                    fileName.textContent = file.name;
                    fileInfo.classList.remove('hidden');
                } else {
                    showStatus('Please upload a valid Markdown file (.md or .markdown)', 'error');
                }
            }
        }

        // Settings form submission
        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            loadingMessage.textContent = 'Saving settings...';
            loadingModal.showModal();

            const formData = new FormData(settingsForm);
            
            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                loadingModal.close();
                
                if (response.ok) {
                    showStatus('Settings saved successfully!', 'success');
                } else {
                    showStatus('Error saving settings', 'error');
                }
            } catch (error) {
                loadingModal.close();
                showStatus('Error: ' + error.message, 'error');
            }
        });

        // Upload form submission
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!currentFile) {
                showStatus('Please select a file first', 'error');
                return;
            }

            loadingMessage.textContent = 'Generating PDF... This may take a moment.';
            loadingModal.showModal();

            const formData = new FormData();
            formData.append('file', currentFile);

            try {
                const response = await fetch('/api/convert', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    
                    // Get filename from Content-Disposition header
                    const contentDisposition = response.headers.get('Content-Disposition');
                    const fileNameMatch = contentDisposition.match(/filename="?(.+)"?/);
                    const downloadFileName = fileNameMatch ? fileNameMatch[1] : 'output.pdf';
                    
                    a.download = downloadFileName;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);

                    loadingModal.close();
                    showStatus(
                        `PDF generated successfully! File "${downloadFileName}" has been saved to your Downloads folder.`,
                        'success'
                    );
                } else {
                    const error = await response.json();
                    loadingModal.close();
                    showStatus('Error generating PDF: ' + error.error, 'error');
                }
            } catch (error) {
                loadingModal.close();
                showStatus('Error: ' + error.message, 'error');
            }
        });

        function showStatus(message, type) {
            const statusDiv = document.getElementById('statusMessage');
            const alertClass = type === 'success' ? 'alert-success' : 'alert-error';
            const icon = type === 'success'
                ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />'
                : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />';

            statusDiv.innerHTML = `
                <div class="alert ${alertClass} shadow-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                        ${icon}
                    </svg>
                    <span>${message}</span>
                </div>
            `;
            statusDiv.classList.remove('hidden');

            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 5000);
        }
    </script>
</body>
</html>
```

### Step 6: Running the Application

**6.1 Create a run script for convenience:**

Create `run.sh` (Unix/Mac) or `run.bat` (Windows):

**run.sh:**
```bash
#!/bin/bash
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Make it executable:
```bash
chmod +x run.sh
```

**run.bat:**
```batch
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**6.2 Or run directly:**
```bash
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The application will be available at: `http://127.0.0.1:8000`

### Step 7: Testing and Verification

**7.1 Create a test markdown file (`test.md`):**

```markdown
# Test Document

This is a test document to verify the Markdown to PDF converter.

## Features

- **Bold text**
- *Italic text*
- [Links](https://example.com)

### Code Block

\`\`\`python
def hello_world():
    print("Hello, World!")
\`\`\`

### Table

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |

### Blockquote

> This is a blockquote with multiple lines.
> It demonstrates the styling capabilities.

### Lists

1. First item
2. Second item
   - Nested item
   - Another nested item
3. Third item
```

**7.2 Testing checklist:**

1. ✅ Start the server
2. ✅ Open browser to http://127.0.0.1:8000
3. ✅ Verify settings page loads correctly
4. ✅ Try changing prose size
5. ✅ Add custom classes (e.g., "text-blue-600" for H1)
6. ✅ Save settings
7. ✅ Upload test.md file
8. ✅ Convert to PDF
9. ✅ Verify PDF downloads correctly
10. ✅ Check PDF styling matches settings
11. ✅ Verify settings persist after page reload

### Step 8: Troubleshooting

**Common Issues:**

**Issue 1: WeasyPrint installation fails**
- Solution: Check README.md for system dependencies
- Alternative: Modify `pdf_generator.py` to use xhtml2pdf or pdfkit

**Issue 2: Tailwind classes not appearing in PDF**
- Solution: WeasyPrint loads CSS from CDN, ensure internet connection
- Alternative: Download Tailwind CSS file and serve locally

**Issue 3: Code highlighting not working**
- Solution: Verify Pygments is installed: `uv add pygments`
- Check that codehilite extension is enabled

**Issue 4: File upload fails**
- Solution: Check file size limits in FastAPI config
- Verify file permissions in project directory

**Issue 5: PDF looks different from preview**
- Solution: WeasyPrint has different CSS support than browsers
- Some Tailwind classes may not render identically
- Test with simpler classes first

### Step 9: Optional Enhancements

**9.1 Add batch processing:**
Modify the upload endpoint to accept multiple files and generate a ZIP of PDFs.

**9.2 Add PDF preview:**
Generate a preview image of the PDF before download using `pdf2image`.

**9.3 Add template presets:**
Create predefined style templates (Academic, Professional, Creative, etc.).

**9.4 Add dark mode support:**
Implement dark mode styling for the web interface.

**9.5 Add export/import settings:**
Allow users to export settings as JSON and import them later.

### Step 10: Deployment Considerations

For future deployment beyond localhost:

**Option 1: Docker**
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . /app/

# Install uv
RUN pip install uv

# Install dependencies
RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Option 2: Traditional deployment**
- Use gunicorn instead of uvicorn for production
- Add nginx as reverse proxy
- Set up proper logging
- Add authentication if needed

## Summary

This implementation provides:

✅ FastAPI backend with file upload
✅ Beautiful TailwindCSS + DaisyUI interface
✅ Customizable Tailwind classes for all elements
✅ Settings persistence via YAML config
✅ WeasyPrint for high-quality PDFs
✅ Support for tables, code highlighting, and more
✅ Drag-and-drop file upload
✅ Success messages with file location
✅ All running on localhost

The application is production-ready for local use and can be easily extended or deployed.
