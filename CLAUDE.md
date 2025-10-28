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
- 22 styleable elements including table components (thead, tbody, tr, td, th)

## Critical Gotchas

### 1. File Reading Bug (`main.py:58`, `get_file_content()`)
**MUST exclude `.tempconfig` AND `.meta` files** when reading markdown content, otherwise JSON gets rendered as HTML.
```python
if f.startswith(file_id) and not f.endswith('.meta') and not f.endswith('.tempconfig'):
```

### 2. Temp Config Flow (Unsaved Settings)
- Frontend sends current config as `temp_config` JSON field when "Generate Without Saving"
- Backend saves to `{uuid}.tempconfig` (`main.py:242-244`)
- Preview checks for `.tempconfig` first, falls back to saved config (`main.py:152-180`)

### 3. Unsaved Changes Detection (`index.html`)
- `checkForChanges()` must compare ALL config fields: prose_size, prose_color, back_to_top_enabled, back_to_top_text, and all custom_classes
- Called after `loadSavedConfig()` to reset `hasUnsavedChanges` flag
- Green (`.input-synced`) vs yellow (`.input-modified`) backgrounds show field sync state

### 4. Prose Size & Color Template (`templates/preview.html`)
Handles both `prose-sm` and `sm` formats, plus optional color:
```html
<article class="prose {% if config.prose_color %}prose-{{ config.prose_color }}{% endif %} {{ config.prose_size if (config.prose_size and config.prose_size.startswith('prose-')) else ('prose-' + (config.prose_size or 'lg')) }}">
```
Tailwind CDN line 9 must include `?plugins=typography` for prose variants.

### 5. Config Resolution (`pdf_generator.py:10-25`)
Checks `~/Library/Application Support/md2pdf/config.yaml` before local `config.yaml`. Creates default config on first launch.

### 6. Back to Top Link (`preview.html`)
- Only renders when `config.back_to_top_enabled` is true
- Uses `@page { @bottom-right { content: "..." } }` CSS for printed pages
- Floating link on screen hidden during print with `.no-print` class
- Requires `#top` anchor at start of content

### 7. Factory Reset Endpoint (`main.py:98`)
Returns hardcoded factory defaults matching `pdf_generator.py:_create_default_config()`. Must be kept in sync when adding new config fields.

### 8. Form Field Tracking (`index.html:fieldNames`)
Array must include ALL element class fields for proper change detection, revert, and factory reset. Currently: 22 fields (h1-h6, p, a, code, pre, blockquote, table, thead, tbody, tr, td, th, ul, ol, li, hr, img).
