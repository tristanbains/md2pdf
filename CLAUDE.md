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
- `main.py` - FastAPI routes, file upload/storage, config/preset management, preview rendering
- `pdf_generator.py` - Markdown→HTML conversion, TailwindCSS class application, config defaults
- `templates/index.html` - Main UI with drag-drop upload, settings form, preset selector, unsaved changes detection
- `templates/preview.html` - Print-optimized preview page with `window.print()` integration

**Core Design Decisions**:
1. **Browser-based PDF generation** via `window.print()` for high-quality output
2. **UUID-based temporary storage** with automatic cleanup via `cleanup_old_files()`
3. **Config locations**: `config.yaml` (dev) or `~/Library/Application Support/md2pdf/config.yaml` (production)
4. **TailwindCSS classes applied server-side** via BeautifulSoup to markdown-rendered HTML
5. **Multi-tier config system**: Temp config (.tempconfig) > Preset markers (.preset) > Backend config.yaml

**File Storage Pattern**:
```
temp_uploads/
  {uuid}.md          # Uploaded markdown content
  {uuid}.meta        # Original filename metadata
  {uuid}.tempconfig  # Temporary unsaved settings (JSON, from "Generate Without Saving")
  {uuid}.preset      # Preset slug marker (from preset selection + upload)
```

## Critical Patterns

### File Reading Must Exclude Metadata
`main.py:get_file_content()` MUST exclude metadata files:
```python
if filename.startswith(file_id) and not filename.endswith(('.meta', '.tempconfig', '.preset')):
```
**Why**: These are metadata, not markdown content. Including them causes JSON/text to be rendered as HTML.

### Preview Config Priority Order
`main.py:/preview/{file_id}` resolves config in this order (highest priority first):
1. `.tempconfig` file (user clicked "Generate Without Saving")
2. `.preset` marker file (user selected preset then uploaded)
3. Backend `config.yaml` (saved settings or loaded preset)

### Factory Reset Source of Truth
When adding config fields, update **ONLY** `pdf_generator.py:get_default_config()`. All other locations derive from this method.

### TailwindCSS Typography Plugin Required
`templates/preview.html` MUST include typography plugin in CDN script tag. Without it, prose classes don't work.

### CodeHilite Theme Names Use Hyphens
Pygments themes use hyphens (e.g., `github-dark`), NOT underscores. Never convert formats.

## Adding Features

### Adding a New Styleable Element
See [docs/development-patterns.md](docs/development-patterns.md#adding-a-new-styleable-element) for complete workflow.

Key touchpoints:
1. `pdf_generator.py:get_default_config()` - Add to custom_classes dict
2. `main.py:update_config()` - Add Form parameter + dict entry
3. `templates/index.html` - Add input field + to fieldNames array
4. `pdf_generator.py:apply_custom_classes()` - Add element handler

### Working with Presets
Preset system detailed in [docs/implementation-details.md](docs/implementation-details.md).

Key points:
- Factory presets (read-only) in `presets/factory/`
- User presets (fully editable) in `presets/user/`
- Preset files are YAML with `_metadata` key
- API endpoints: `/api/presets/*` (list, save, load, delete, export, import)

## Documentation

Detailed technical information:
- **[docs/implementation-details.md](docs/implementation-details.md)** - Config flow, preset system, prose logic, unsaved changes detection
- **[docs/development-patterns.md](docs/development-patterns.md)** - Workflows, debugging, testing patterns

## Platform Notes

**macOS-Specific**: Build with py2app, config in `~/Library/Application Support/md2pdf/`
**Cross-Platform**: Core app runs anywhere with uv, but build process is macOS only
