# Markdown to PDF Converter

A FastAPI web application that converts Markdown files to styled PDFs using TailwindCSS.

## System Dependencies for WeasyPrint

WeasyPrint requires system libraries to be installed before running the application.

### macOS (using Homebrew)
```bash
brew install python3 cairo pango gdk-pixbuf libffi
```

### Ubuntu/Debian
```bash
sudo apt-get install python3-dev python3-pip python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

### Windows
Download and install GTK3 runtime from:
https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

Or use Windows Subsystem for Linux (WSL) with Ubuntu instructions.

## Installation

1. Install system dependencies (see above)
2. Install Python dependencies:
```bash
uv sync
```

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

## Running the Application

Start the development server:
```bash
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The application will be available at: http://127.0.0.1:8000

## Features

- Web-based interface for uploading Markdown files
- Customizable TailwindCSS styling for all markdown elements
- Settings persistence via YAML configuration
- High-quality PDF generation with syntax highlighting
- Drag-and-drop file upload
- Support for tables, code blocks, and more

## Usage

1. Open http://127.0.0.1:8000 in your browser
2. Customize PDF styling settings (optional)
3. Upload a Markdown file (.md or .markdown)
4. Click "Convert to PDF" to generate and download the PDF