# CLAUDE.md

FastAPI app serving browser-based markdown-to-PDF conversion. Uses `window.print()` for PDF generation, not server-side libraries.

## Architecture

**Stack**: FastAPI + Jinja2 templates + TailwindCSS Typography + Python-Markdown
**Commands**: `make restart` (dev), `make build` (macOS app), `uv sync` (deps)

**Key Design**:
- Browser PDF via `window.print()` (not WeasyPrint/xhtml2pdf)
- UUID-based temp file storage with `.meta` (filename) and `.tempconfig` (unsaved settings)
- Config locations: `config.yaml` (dev) or `~/Library/Application Support/md2pdf/config.yaml` (distributed)
- TailwindCSS classes applied to markdown elements via BeautifulSoup

## Critical Gotchas

### 1. File Reading Bug (`main.py:58`, `get_file_content()`)
**MUST exclude `.tempconfig` AND `.meta` files** when reading markdown content, otherwise JSON gets rendered as HTML.
```python
if f.startswith(file_id) and not f.endswith('.meta') and not f.endswith('.tempconfig'):
```

### 2. Temp Config Flow (Unsaved Settings)
- Frontend sends current config as `temp_config` JSON field when "Generate Without Saving"
- Backend saves to `{uuid}.tempconfig` (`main.py:207-210`)
- Preview checks for `.tempconfig` first, falls back to saved config (`main.py:155-171`)

### 3. Unsaved Changes Detection (`index.html`)
- `checkForChanges()` must be called after `loadSavedConfig()` on line 500 to reset `hasUnsavedChanges` flag
- Green (`.input-synced`) vs yellow (`.input-modified`) backgrounds show config state

### 4. Prose Size Template (`templates/preview.html`)
Handles both `prose-sm` and `sm` formats:
```html
<article class="prose {{ config.prose_size if (config.prose_size and config.prose_size.startswith('prose-')) else ('prose-' + (config.prose_size or 'lg')) }}">
```
Tailwind CDN line 9 must include `?plugins=typography` for prose variants.

### 5. Config Resolution (`pdf_generator.py:10-25`)
Checks `~/Library/Application Support/md2pdf/config.yaml` before local `config.yaml`. Creates default config on first launch.
