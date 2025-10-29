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

# Manual server start
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Architecture Overview

**Stack**: FastAPI + Jinja2 templates + TailwindCSS Typography + Python-Markdown + BeautifulSoup

**Key Components**:
- `main.py` - FastAPI routes, file upload/storage, config management, preview rendering
- `pdf_generator.py` - Markdown→HTML conversion, TailwindCSS class application, config management
- `templates/index.html` - Main UI with drag-drop upload, settings form, unsaved changes detection
- `templates/preview.html` - Print-optimized preview page with `window.print()` integration

**Core Design Decisions**:
1. **Browser-based PDF generation** via `window.print()` (not WeasyPrint/xhtml2pdf) for high-quality output
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

## Critical Implementation Details

### 1. File Reading Must Exclude Metadata Files
`main.py:70` in `get_file_content()` **MUST exclude `.tempconfig` AND `.meta` files**, otherwise JSON gets rendered as HTML:
```python
if filename.startswith(file_id) and not filename.endswith(('.meta', '.tempconfig')):
```

### 2. Temp Config Flow (Unsaved Settings)
**Frontend → Backend → Preview** workflow:
1. User clicks "Generate Without Saving"
2. `index.html` calls `getCurrentConfig()` to collect all form values including `prose_color`
3. Frontend sends config as `temp_config` JSON field in FormData
4. Backend saves to `{uuid}.tempconfig` (around `main.py:240`)
5. Preview route (`main.py:191-250`) checks for `.tempconfig` first, falls back to saved config
6. If found, loads JSON and sets `pdf_gen.config = temp_config`

### 3. Unsaved Changes Detection System
`index.html` JavaScript requirements:
- **`savedConfig` object**: Loaded from `/api/config` on page load
- **`checkForChanges()`**: Compares ALL fields (prose_size, prose_color, all 22 custom_classes)
- **Visual indicators**: Green (`.input-synced`) vs yellow (`.input-modified`) backgrounds
- **`fieldNames` array** (line ~390): MUST include all 22 element class field IDs
- Call `checkForChanges()` after `loadSavedConfig()` to reset `hasUnsavedChanges` flag

### 4. Prose Template Logic (Critical!)
`templates/preview.html:183` - The `<article>` tag class generation:

**Prose Size Handling**:
```jinja2
{{ config.prose_size if (config.prose_size and (config.prose_size == 'prose' or config.prose_size.startswith('prose-'))) else ('prose-' + (config.prose_size or 'lg')) }}
```
- Accepts: "prose", "prose-sm", "prose-lg", etc. → outputs as-is
- Legacy: "sm", "lg" → prepends "prose-" → outputs "prose-sm", "prose-lg"
- **Critical**: Must handle exact "prose" OR "prose-*" to avoid "prose-prose" bug

**Prose Color Handling**:
```jinja2
{{ config.prose_color if config.prose_color.startswith('prose-') else 'prose-' + config.prose_color }}
```
- Accepts: "prose-slate" → outputs "prose-slate"
- Legacy: "slate" → prepends "prose-" → outputs "prose-slate"

**CRITICAL CSS SPECIFICITY ISSUE**: Prose colors (prose-slate, prose-zinc, prose-stone) only work when `custom_classes` are empty or use non-color utilities. Custom `text-*` color classes override prose color schemes due to higher CSS specificity. Example:
- ✅ `custom_classes.h1 = "font-bold text-4xl"` → prose color applies
- ❌ `custom_classes.h1 = "text-blue-900 font-bold"` → prose color overridden

### 5. Config Resolution Order
`pdf_generator.py:10-25` checks in this order:
1. `~/Library/Application Support/md2pdf/config.yaml` (production)
2. `config.yaml` (development)
3. If neither exists, creates default in Application Support

### 6. Factory Reset Configuration
`main.py:94-103` factory reset endpoint uses `PDFGenerator.get_default_config()` as the single source of truth. When adding new config fields, update only `pdf_generator.py:52-90` `get_default_config()` method.

### 7. Form Field Tracking Requirements
`index.html:390` `fieldNames` array tracks ALL styleable elements for:
- Change detection (green/yellow backgrounds)
- Revert to saved functionality
- Factory reset
- Temp config collection

**Current 22 fields**: h1_classes, h2_classes, h3_classes, h4_classes, h5_classes, h6_classes, p_classes, a_classes, code_classes, pre_classes, blockquote_classes, table_classes, thead_classes, tbody_classes, tr_classes, td_classes, th_classes, ul_classes, ol_classes, li_classes, hr_classes, img_classes

### 8. TailwindCSS Typography Plugin Requirement
`templates/preview.html:9` MUST include typography plugin:
```html
<script src="https://cdn.tailwindcss.com?plugins=typography"></script>
```
Without `?plugins=typography`, prose classes won't work.

## Common Development Patterns

### Adding a New Styleable Element
1. Add field to `pdf_generator.py:get_default_config()` custom_classes dict (single source of truth)
2. Add `{element}_classes: str = Form("")` to `main.py:update_config()` parameters
3. Add field to `main.py:update_config()` custom_classes dict assembly
4. Add input field to `templates/index.html` with `id="{element}_classes"`
5. Add `"{element}_classes"` to `index.html:fieldNames` array
6. Add element handling to `pdf_generator.py:apply_custom_classes()`

### Debugging Temp Config Issues
1. Check `temp_uploads/{uuid}.tempconfig` contains expected JSON
2. Verify `prose_color` field is present in tempconfig
3. Check browser DevTools Network tab for FormData contents
4. Add debug prints in `main.py:191-226` to trace config loading
5. Inspect rendered `<article>` tag in browser to verify classes applied

### Testing Prose Colors
Prose colors have SUBTLE differences between grayscale variants (slate/zinc/stone). For obvious testing:
- Use `prose-invert` for dramatic contrast (inverts all colors)
- Ensure ALL custom_classes are empty (no `text-*`, `bg-*`, `border-*` color utilities)
- Compare headings and links side-by-side
- Use browser DevTools to verify correct classes in `<article>` tag

## Platform Limitations

### macOS-Specific Features
- **Build process** (`make build`): Uses py2app which only works on macOS for creating .app bundles
- **Config file location**: Currently hardcoded to `~/Library/Application Support/md2pdf/`
  - Works on macOS
  - Will create this path on Linux/Windows but may not follow platform conventions
  - Linux convention: `~/.config/md2pdf/` or `~/.local/share/md2pdf/`
  - Windows convention: `%APPDATA%\md2pdf\`

### Cross-Platform Development
- **Running the app**: Works on any platform with uv installed
- **All commands use uv**: Consistent Python environment across platforms
- **Core functionality**: Fully portable (FastAPI, markdown processing, browser-based PDF)
- **WeasyPrint**: Optional feature requiring platform-specific system dependencies
