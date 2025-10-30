# Implementation Details

Deep technical reference for MD2PDF's critical implementation patterns. Consult this when debugging edge cases or working on core features.

## File Reading Must Exclude Metadata Files

`main.py:70` in `get_file_content()` **MUST exclude `.tempconfig` AND `.meta` files**, otherwise JSON gets rendered as HTML:
```python
if filename.startswith(file_id) and not filename.endswith(('.meta', '.tempconfig')):
```

## Temp Config Flow (Unsaved Settings)

**Frontend → Backend → Preview** workflow:
1. User clicks "Generate Without Saving"
2. `index.html` calls `getCurrentConfig()` to collect all form values including `prose_color`
3. Frontend sends config as `temp_config` JSON field in FormData
4. Backend saves to `{uuid}.tempconfig` (around `main.py:240`)
5. Preview route (`main.py:191-250`) checks for `.tempconfig` first, falls back to saved config
6. If found, loads JSON and sets `pdf_gen.config = temp_config`

## Unsaved Changes Detection System

`index.html` JavaScript requirements:
- **`savedConfig` object**: Loaded from `/api/config` on page load
- **`checkForChanges()`**: Compares ALL fields (prose_size, prose_color, all 22 custom_classes)
- **Visual indicators**: Green (`.input-synced`) vs yellow (`.input-modified`) backgrounds
- **`fieldNames` array** (line ~390): MUST include all 22 element class field IDs
- Call `checkForChanges()` after `loadSavedConfig()` to reset `hasUnsavedChanges` flag

## Prose Template Logic (Critical!)

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

## Config Resolution Order

`pdf_generator.py:10-25` checks in this order:
1. `~/Library/Application Support/md2pdf/config.yaml` (production)
2. `config.yaml` (development)
3. If neither exists, creates default in Application Support

## Factory Reset Configuration

`main.py:94-103` factory reset endpoint uses `PDFGenerator.get_default_config()` as the single source of truth. When adding new config fields, update only `pdf_generator.py:52-90` `get_default_config()` method.

## Form Field Tracking Requirements

`index.html:455` `fieldNames` array tracks ALL styleable elements AND code container fields for:
- Change detection (green/yellow backgrounds)
- Revert to saved functionality
- Factory reset
- Temp config collection

**Current 25 fields**:
- **22 element class fields**: h1_classes, h2_classes, h3_classes, h4_classes, h5_classes, h6_classes, p_classes, a_classes, code_classes, pre_classes, blockquote_classes, table_classes, thead_classes, tbody_classes, tr_classes, td_classes, th_classes, ul_classes, ol_classes, li_classes, hr_classes, img_classes
- **3 code container fields**: codehilite_auto_bg, codehilite_custom_bg, codehilite_wrapper_classes

## TailwindCSS Typography Plugin Requirement

`templates/preview.html:9` MUST include typography plugin:
```html
<script src="https://cdn.tailwindcss.com?plugins=typography"></script>
```
Without `?plugins=typography`, prose classes won't work.

## CodeHilite Theme System (Syntax Highlighting)

**CRITICAL**: Pygments theme names use **hyphens** (e.g., `github-dark`, `one-dark`), NOT underscores. Never convert between formats - keep native Pygments format throughout the system.

**Architecture**:
- `pdf_generator.py:get_codehilite_css()` generates dynamic CSS from Pygments themes
- `pdf_generator.py:get_available_themes()` returns ALL Pygments themes (~30)
- `main.py:/theme-preview` route displays all themes with scoped CSS
- `main.py:/` home route passes `available_themes` to template
- `templates/theme_preview.html` shows live code samples with postMessage communication
- `templates/index.html` dropdown dynamically generated from `available_themes`

**CRITICAL - Dynamic Dropdown Population**:
The dropdown MUST be dynamically generated from `available_themes` passed from backend:
```jinja2
<select name="codehilite_theme" id="codehilite_theme">
    {% for theme in available_themes %}
    <option value="{{ theme }}" {% if config.codehilite_theme == theme %}selected{% endif %}>
        {{ theme.replace('-', ' ').replace('_', ' ').title() }}
    </option>
    {% endfor %}
</select>
```

**Why This Matters**:
- Theme preview shows ALL Pygments themes
- If dropdown is hardcoded with only some themes, selecting unlisted themes from preview will fail silently
- Dropdown value becomes empty, causing `pygments.styles.` error

**Theme Name Flow**:
1. `get_all_styles()` returns: "github-dark" (hyphens)
2. Backend passes to template: `available_themes = ["default", "monokai", "github-dark", ...]`
3. Dropdown renders: `<option value="github-dark">` (hyphens)
4. Config saves: `codehilite_theme: "github-dark"` (hyphens)
5. Pygments receives: "github-dark" (hyphens)

**Theme Preview Gallery**:
- Each theme gets scoped CSS: `.theme-github_dark .codehilite { ... }`
- Scope prefix generated in `main.py:271`: `.theme-{name.replace('.', '_').replace('-', '_')}`
- CSS scoping done in `pdf_generator.py:145-158` via regex selector transformation
- Clicking theme card sends postMessage with theme name (unchanged)
- Main page receives theme and updates dropdown via `window.opener.postMessage()`
- Dropdown selection now guaranteed to succeed because ALL themes are included

**Adding Theme Support**:
1. `get_codehilite_css(theme_name, scope_prefix)` - generates CSS with optional scoping
2. `markdown_to_html()` - passes theme to CodeHilite extension via `extension_configs`
3. Never add format conversions - Pygments handles its own theme names
4. New themes automatically appear in dropdown via dynamic generation

## Code Block Container Configuration

**Purpose**: Provides control over code block wrapper styling using TailwindCSS classes with exact background color matching from Pygments themes.

**Architecture**:
- Config stored in `codehilite_container` dict in `config.yaml`
- Auto-detects exact theme background color from Pygments themes via `formatter.style.background_color`
- Allows manual override with custom hex colors
- Applies TailwindCSS classes + inline background style directly to `.codehilite` divs via BeautifulSoup
- GUI controls in `templates/index.html` "Code Block Container" section (positioned AFTER Element Styling)

**Config Structure** (`pdf_generator.py:50-54`):
```python
'codehilite_container': {
    'auto_background': True,                              # Auto-detect exact bg from theme
    'custom_background': '',                              # Manual hex override (e.g., "#272822")
    'wrapper_classes': 'p-4 rounded-lg overflow-x-auto my-4'  # TailwindCSS classes
}
```

**Background Auto-Detection** (`pdf_generator.py:223-270`):
The `apply_codehilite_wrapper_styling()` method applies styling directly to HTML:

Priority order for background:
1. If `custom_background` is set → use it (highest priority)
2. Else if `auto_background` is True → extract exact color from Pygments theme via `HtmlFormatter(style=theme_name).style.background_color`
3. Else → no background applied

Example theme backgrounds:
- monokai → `#272822` (dark gray-green)
- dracula → `#282a36` (dark blue-gray)
- github-dark → `#0d1117` (near-black)
- default → `#f8f8f8` (light gray)

**Why This Matters**:
- Dark themes have dark backgrounds in their Pygments style definitions
- Auto-detection ensures exact theme color matching (e.g., monokai → precisely `#272822`)
- Previous approach with hardcoded CSS generated "slightly off" colors
- Background applied as inline style to ensure correct rendering without CSS specificity issues

**DOM Structure** (after BeautifulSoup processing):
```html
<div class="codehilite p-4 rounded-lg overflow-x-auto my-4" style="background-color: #272822;">
    <pre class="<custom_classes.pre>">
        <code>...</code>
    </pre>
</div>
```

**Processing Flow** (`main.py:217-223`):
```python
html_body = pdf_gen.markdown_to_html(markdown_content)
html_body = pdf_gen.apply_custom_classes(html_body)
html_body = pdf_gen.apply_codehilite_wrapper_styling(html_body)  # Applied AFTER custom classes
```

**GUI Controls** (`templates/index.html:312-353`):
Located AFTER Element Styling grid (not before):
- Checkbox: "Auto-match theme background" (checked by default)
  - Help text: "Automatically use exact background color from Pygments theme (monokai → #272822, dracula → #282a36, etc.)"
- Text input: "Custom Background (optional)"
  - Placeholder: "#272822"
  - Help text: "Hex color (overrides auto-detect). Leave empty to use theme background."
- Text input: "Code Block Container Classes"
  - Default: "p-4 rounded-lg overflow-x-auto my-4"
  - Placeholder: "p-4 rounded-lg overflow-x-auto my-4"
  - Help text: "Tailwind CSS classes for code block wrapper (e.g., p-4 rounded-lg shadow-md overflow-x-auto)"

**Field Tracking** (`templates/index.html:455`):
Fields added to `fieldNames` array:
- `codehilite_auto_bg`
- `codehilite_custom_bg`
- `codehilite_wrapper_classes`

**Change Detection** (`templates/index.html:478-483`):
```javascript
const container = savedConfig.codehilite_container || {};
hasChanges = hasChanges ||
    document.getElementById('codehilite_auto_bg').checked !== (container.auto_background !== false) ||
    document.getElementById('codehilite_custom_bg').value.trim() !== (container.custom_background || '') ||
    document.getElementById('codehilite_wrapper_classes').value.trim() !== (container.wrapper_classes || 'p-4 rounded-lg overflow-x-auto my-4');
```

**Temp Config Flow** (`templates/index.html:558-562`):
```javascript
codehilite_container: {
    auto_background: document.getElementById('codehilite_auto_bg').checked,
    custom_background: document.getElementById('codehilite_custom_bg').value.trim(),
    wrapper_classes: document.getElementById('codehilite_wrapper_classes').value.trim()
}
```

**Factory Reset** (`main.py:101-107`):
Includes `codehilite_container` in factory reset endpoint response

**API Integration** (`main.py:114-116, 144-148`):
- Form parameters: `codehilite_auto_bg: bool`, `codehilite_custom_bg: str`, `codehilite_wrapper_classes: str`
- Assembled into `codehilite_container` dict before passing to `pdf_gen.update_config()`

**Config Migration** (`pdf_generator.py:33-40`):
Automatically adds `codehilite_container` to old configs on load:
```python
if 'codehilite_container' not in config:
    default_config = self.get_default_config()
    config['codehilite_container'] = default_config['codehilite_container']
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
```

**Testing Dark Themes**:
1. Select a dark theme (e.g., monokai, dracula, github-dark, nord)
2. Ensure "Auto-match theme background" is checked
3. Generate preview → code blocks should have exact theme background color
4. Right-click code block → Inspect Element → verify `style="background-color: #272822;"` (or theme-specific color)
5. Test custom override: uncheck auto-detect, enter `#1e1e1e` → verify custom background applied
6. Test Tailwind classes: add `shadow-xl border border-gray-700` → verify classes appear in rendered HTML
