# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

FastAPI app serving browser-based markdown-to-PDF conversion. Uses `window.print()` for PDF generation, not server-side libraries.

## Commands

```bash
# Development
make restart          # Kill existing server, start new one, open browser
make dev              # Start server in foreground with logs (port 8000)
uv sync               # Install/sync dependencies

# Building
make install-deps     # Install py2app for building
make build            # Build macOS .app → dist/MD2PDF.app
make clean            # Remove build artifacts

# Git
make git-quick m="commit message"  # Add all files, commit, and push
```

## Architecture Overview

**Stack**: FastAPI + Jinja2 templates + TailwindCSS Typography + Python-Markdown + BeautifulSoup

**Key Components**:
- `main.py` - FastAPI routes, file upload/storage, config management, preview rendering
- `pdf_generator.py` - Markdown→HTML conversion, TailwindCSS class application, config management
- `templates/index.html` - Main UI with drag-drop upload, settings form, unsaved changes detection
- `templates/preview.html` - Print-optimized preview page with `window.print()` integration

**Core Design Decisions**:
1. **Browser-based PDF generation** via `window.print()` for high-quality output
2. **UUID-based temporary storage** with automatic 24-hour cleanup
3. **Dual config locations**: `config.yaml` (dev) or `~/Library/Application Support/md2pdf/config.yaml` (production)
4. **TailwindCSS classes applied server-side** via BeautifulSoup to markdown-rendered HTML
5. **Temp config system** allows "Generate Without Saving" by storing unsaved settings in `.tempconfig` files

**File Storage Pattern**:
```
temp_uploads/
  {uuid}.md          # Uploaded markdown content
  {uuid}.meta        # Original filename
  {uuid}.tempconfig  # Temporary unsaved settings (JSON)
```

## Critical Gotchas

### File Reading Must Exclude Metadata
`main.py:70` in `get_file_content()` MUST exclude `.tempconfig` AND `.meta` files:
```python
if filename.startswith(file_id) and not filename.endswith(('.meta', '.tempconfig')):
```

### Prose Template Logic
`templates/preview.html:183` - Prose size/color handling is delicate:
- Must handle "prose", "prose-sm", "prose-lg" formats to avoid "prose-prose" bug
- Prose colors (prose-slate, prose-zinc) get overridden by `text-*` color classes in custom_classes
- See [docs/implementation-details.md](docs/implementation-details.md#prose-template-logic-critical) for full details

### TailwindCSS Typography Plugin Required
`templates/preview.html:9` MUST include typography plugin:
```html
<script src="https://cdn.tailwindcss.com?plugins=typography"></script>
```

### CodeHilite Theme Names
Pygments theme names use **hyphens** (e.g., `github-dark`), NOT underscores. Never convert formats.

### Factory Reset Source of Truth
When adding config fields, update ONLY `pdf_generator.py:get_default_config()` method.

## Quick Reference

### Adding a New Styleable Element
1. Add field to `pdf_generator.py:get_default_config()` custom_classes dict
2. Add `{element}_classes: str = Form("")` to `main.py:update_config()` parameters
3. Add field to `main.py:update_config()` custom_classes dict assembly
4. Add input field to `templates/index.html` with `id="{element}_classes"`
5. Add `"{element}_classes"` to `index.html:fieldNames` array
6. Add element handling to `pdf_generator.py:apply_custom_classes()`

See [docs/development-patterns.md](docs/development-patterns.md#adding-a-new-styleable-element) for detailed example.

### Config Resolution Order
1. `~/Library/Application Support/md2pdf/config.yaml` (production)
2. `config.yaml` (development)
3. If neither exists, creates default in Application Support

### Form Field Tracking
`index.html:455` `fieldNames` array tracks **25 fields total**:
- 22 element class fields (h1_classes through img_classes)
- 3 code container fields (codehilite_auto_bg, codehilite_custom_bg, codehilite_wrapper_classes)

## Documentation

For detailed technical information, see:
- **[docs/implementation-details.md](docs/implementation-details.md)** - Deep dive on temp config flow, CodeHilite themes, code container config, unsaved changes detection
- **[docs/development-patterns.md](docs/development-patterns.md)** - Common workflows, debugging strategies, testing patterns

## Platform Notes

### macOS-Specific
- Build process (`make build`) uses py2app (macOS only)
- Config location defaults to `~/Library/Application Support/md2pdf/`

### Cross-Platform
- Running the app works on any platform with uv
- Core functionality fully portable (FastAPI, markdown, browser PDF)
- Linux/Windows config paths may not follow platform conventions
