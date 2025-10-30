# Markdown to PDF Converter

A FastAPI web application that converts Markdown files to styled PDFs using browser-based PDF generation. Features comprehensive TailwindCSS styling controls, real-time preview, and persistent configuration.

## Quick Start

```bash
# Install dependencies
uv sync

# Start development server
make restart
# or manually:
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The application will open automatically at http://127.0.0.1:8000

## Running the Application

Start the development server:
```bash
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The application will be available at: http://127.0.0.1:8000

## Features

### Core Functionality
- **Browser-based PDF Generation**: Uses `window.print()` for high-quality PDFs without server-side dependencies
- **Real-time Preview**: HTML preview with print-optimized styling before saving
- **Drag-and-drop Upload**: Easy file upload with visual feedback
- **Temporary File Storage**: UUID-based storage with automatic 24-hour cleanup

### Styling & Configuration
- **Comprehensive Element Styling**: Customize TailwindCSS classes for 22 markdown elements:
  - Headings (h1-h6), paragraphs, links, code blocks, inline code
  - Tables and table components (table, thead, tbody, tr, td, th)
  - Lists (ul, ol, li), blockquotes, horizontal rules, images
- **Prose Size Control**: Choose from prose-sm to prose-2xl
- **Prose Color Variants**: Apply color themes (zinc, slate, gray, etc.)
- **Back to Top Link**: Optional link on each printed page (customizable text)
- **Settings Persistence**: Configuration saved to YAML file
- **Factory Reset**: Restore all settings to defaults with one click

### Advanced Features
- **Unsaved Changes Detection**: Visual indicators (green/yellow backgrounds) show modified settings
- **Temporary Config Support**: Generate PDFs with unsaved settings without affecting saved config
- **Syntax Highlighting**: Automatic code syntax highlighting with multiple language support
- **Markdown Extensions**: Support for tables, footnotes, table of contents, definition lists, and more

### User Experience
- **Clean Filename Handling**: PDFs saved with original filename (no UUID prefix)
- **Keyboard Shortcuts**: Cmd/Ctrl+P for quick printing
- **Responsive Design**: Works on desktop and mobile browsers
- **Collapsible Settings**: Keep interface clean while providing full control

## Usage

1. **Open** http://127.0.0.1:8000 in your browser
2. **Configure Styling** (optional):
   - Expand "PDF Styling Settings" section
   - Adjust prose size, color, and element-specific classes
   - Enable/disable back-to-top link
   - Save settings or use factory reset
3. **Upload Markdown**:
   - Drag and drop a .md/.markdown file, or
   - Click "Browse Files" to select
4. **Generate PDF**:
   - Click "Generate Preview" to see styled HTML
   - Use "Print/Save as PDF" button
   - Select "Save as PDF" as destination
   - Confirm filename and save location

### Workflow Options

**Option 1: Save Settings for Reuse**
- Configure styles → Save Settings → Upload file → Generate

**Option 2: One-time Styling**
- Configure styles → Upload file → Generate Without Saving

**Option 3: Use Saved Settings**
- Upload file → Generate (uses last saved settings)

## Configuration

Settings are stored in `config.yaml` (development) or `~/Library/Application Support/md2pdf/config.yaml` (distributed app).

### Configuration Structure
```yaml
prose_size: prose
prose_color: zinc
back_to_top_enabled: false
back_to_top_text: "↑ Top"
custom_classes:
  h1: text-gray-900 font-bold
  h2: text-gray-800 font-semibold
  td: border border-gray-200 px-4 py-2
  # ... all element classes
```

### Factory Defaults
The app includes sensible defaults with academic styling:
- Clean typography with proper hierarchy
- Bordered tables with padding
- Syntax-highlighted code blocks
- Blue hyperlinks with hover effects

## Building for Distribution

```bash
# Install build dependencies (first time only)
make install-deps

# Build macOS .app
make build

# Output: dist/MD2PDF.app
```

The built app bundles all dependencies and uses system config location.