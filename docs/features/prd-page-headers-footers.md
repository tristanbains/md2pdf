# PRD: Custom Page Headers & Footers

**Feature ID**: `FEAT-002`
**Status**: Planned
**Priority**: High
**Complexity**: High (5-6 hours)
**Risk Level**: Medium

---

## Executive Summary

Add customizable headers and footers that appear on every page of generated PDFs. Users can define custom text with template variables (`{page}`, `{total_pages}`, `{filename}`, `{date}`), configure styling and alignment, and enable automatic page numbering. Implementation uses HTML structure injection for maximum browser compatibility rather than CSS `@page` rules.

---

## Problem Statement

### Current Limitations
- No way to add branding, titles, or identification to PDFs
- Page numbers must be manually added to markdown content
- Cannot add consistent headers/footers across all pages
- Professional documents require letterhead-style formatting
- No date/filename information on printed pages

### User Pain Points
1. **Professional Documents**: Legal, academic, and business documents need headers/footers
2. **Page Navigation**: Readers need page numbers for reference and navigation
3. **Document Identification**: No easy way to add document title, date, or version
4. **Branding**: Companies need to add logos or company names to PDFs
5. **Manual Workarounds**: Users must edit markdown to add page info (doesn't work for multi-page)

---

## Goals & Success Metrics

### Primary Goals
1. Enable users to add custom text headers and footers to all pages
2. Support dynamic content (page numbers, filename, date)
3. Provide styling controls (alignment, font size, colors)
4. Maintain print quality and pagination

### Success Metrics
- 50%+ of users enable headers or footers
- Page numbering is most-used template variable (estimated 80% of header/footer users)
- Zero pagination issues reported
- Headers/footers display consistently across browsers (Chrome, Safari, Firefox)

### Non-Goals (Out of Scope)
- Images in headers/footers (text only for MVP)
- Different headers for first page vs subsequent pages
- Different headers for odd/even pages
- Section-specific headers (all pages use same header/footer)

---

## User Stories & Use Cases

### User Story 1: Academic Paper
**As an** academic researcher
**I want to** add page numbers and paper title to every page
**So that** my submissions meet journal formatting requirements

**Example**:
- Header: "Climate Change Impact Study - January 2025"
- Footer: "Page {page} of {total_pages}"

**Acceptance Criteria**:
- Can enable header with custom text
- Can use `{page}` and `{total_pages}` variables
- Text appears on all pages consistently

### User Story 2: Company Report
**As a** corporate report writer
**I want to** add company name header and confidentiality footer
**So that** all pages are branded and marked as confidential

**Example**:
- Header: "Acme Corp - Quarterly Report"
- Footer: "Confidential - Internal Use Only"

**Acceptance Criteria**:
- Can enable both header and footer
- Text can be customized
- Alignment options available (left, center, right)

### User Story 3: Technical Documentation
**As a** software developer
**I want to** add filename and date to footer
**So that** printed docs can be tracked and versioned

**Example**:
- Header: (none)
- Footer: "{filename} - Generated on {date}"

**Acceptance Criteria**:
- Can use `{filename}` variable (original uploaded filename)
- Can use `{date}` variable (generation date)
- Can disable header while keeping footer

---

## Technical Specifications

### Architecture Overview

**Approach**: HTML structure injection (not CSS `@page`)

**Rationale**:
- CSS `@page` support is inconsistent across browsers
- `@page` doesn't support dynamic content like page counters reliably
- HTML structure works in all browsers via `window.print()`
- More control over styling and positioning

**Implementation Strategy**:
1. Add header/footer configuration to settings
2. Inject header/footer HTML into preview template
3. Use fixed positioning with print media queries
4. JavaScript page counter for `{page}` and `{total_pages}` variables

---

### Configuration Schema

Add to `pdf_generator.py:get_default_config()`:

```python
'page_headers': {
    'enabled': False,
    'content': '',                     # Plain text with template variables
    'alignment': 'center',             # 'left', 'center', 'right'
    'font_size': '12px',
    'text_color': '#666666',
    'background_color': '',            # Optional background
    'padding': '10px 20px',
    'border_bottom': '',               # CSS border (e.g., '1px solid #ccc')
},
'page_footers': {
    'enabled': False,
    'content': '',                     # Plain text with template variables
    'alignment': 'center',             # 'left', 'center', 'right'
    'font_size': '12px',
    'text_color': '#666666',
    'background_color': '',            # Optional background
    'padding': '10px 20px',
    'border_top': '',                  # CSS border (e.g., '1px solid #ccc')
    'show_page_numbers': False,        # Auto-add "Page X of Y"
}
```

---

### Template Variables

Users can use these placeholders in header/footer content:

| Variable | Description | Example Output |
|----------|-------------|----------------|
| `{page}` | Current page number | `1`, `2`, `3` |
| `{total_pages}` | Total number of pages | `10` |
| `{filename}` | Original uploaded filename | `report.md` |
| `{date}` | Current date (ISO format) | `2025-01-15` |
| `{time}` | Current time (24h format) | `14:30` |
| `{datetime}` | Date and time | `2025-01-15 14:30` |

**Example Usage**:
- `"Page {page} of {total_pages}"` → "Page 2 of 10"
- `"{filename} - Generated on {date}"` → "report.md - Generated on 2025-01-15"
- `"Confidential - Page {page}"` → "Confidential - Page 3"

---

### Template Variable Replacement

**Python Backend** (`pdf_generator.py`):
```python
def apply_template_variables(
    self,
    content: str,
    filename: str = "",
    current_page: int = 0,
    total_pages: int = 0
) -> str:
    """Replace template variables in header/footer content"""
    from datetime import datetime

    now = datetime.now()

    replacements = {
        '{filename}': filename,
        '{date}': now.strftime('%Y-%m-%d'),
        '{time}': now.strftime('%H:%M'),
        '{datetime}': now.strftime('%Y-%m-%d %H:%M'),
        '{page}': str(current_page),           # Placeholder (replaced by JS)
        '{total_pages}': str(total_pages),     # Placeholder (replaced by JS)
    }

    result = content
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)

    return result
```

**JavaScript Frontend** (for page counters):
```javascript
// Page counters are handled client-side after rendering
function updatePageCounters() {
    // Calculate total pages based on document height
    const pageHeight = 1056; // A4 height in pixels at 96dpi
    const contentHeight = document.getElementById('content').offsetHeight;
    const totalPages = Math.ceil(contentHeight / pageHeight);

    // Replace {page} and {total_pages} in headers/footers
    document.querySelectorAll('.page-header, .page-footer').forEach((el, index) => {
        const currentPage = Math.floor(index / 2) + 1; // Approximate
        el.innerHTML = el.innerHTML
            .replace('{page}', currentPage)
            .replace('{total_pages}', totalPages);
    });
}

window.addEventListener('load', updatePageCounters);
```

**Note**: Page counting in browser print is approximate. True page numbers require server-side PDF generation libraries (future enhancement).

---

### HTML Structure

**Template Changes** (`templates/preview.html`):

```html
<body>
    <!-- Header (if enabled) -->
    {% if config.page_headers.enabled %}
    <div class="page-header no-print-hide" style="
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        text-align: {{ config.page_headers.alignment }};
        font-size: {{ config.page_headers.font_size }};
        color: {{ config.page_headers.text_color }};
        background-color: {{ config.page_headers.background_color }};
        padding: {{ config.page_headers.padding }};
        border-bottom: {{ config.page_headers.border_bottom }};
        z-index: 1000;
    ">
        {{ header_content | safe }}
    </div>
    {% endif %}

    <!-- Main Content -->
    <div id="content" style="
        margin-top: {% if config.page_headers.enabled %}60px{% else %}0{% endif %};
        margin-bottom: {% if config.page_footers.enabled %}60px{% else %}0{% endif %};
    ">
        <article class="prose {{ prose_size }} {{ prose_color }}">
            {{ html_content | safe }}
        </article>
    </div>

    <!-- Footer (if enabled) -->
    {% if config.page_footers.enabled %}
    <div class="page-footer no-print-hide" style="
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        text-align: {{ config.page_footers.alignment }};
        font-size: {{ config.page_footers.font_size }};
        color: {{ config.page_footers.text_color }};
        background-color: {{ config.page_footers.background_color }};
        padding: {{ config.page_footers.padding }};
        border-top: {{ config.page_footers.border_top }};
        z-index: 1000;
    ">
        {{ footer_content | safe }}
    </div>
    {% endif %}
</body>
```

---

### Print Media Queries

**CSS for Print** (`templates/preview.html`):

```css
@media print {
    /* Ensure headers/footers appear on every page */
    .page-header, .page-footer {
        position: fixed !important;
    }

    .page-header {
        top: 0 !important;
    }

    .page-footer {
        bottom: 0 !important;
    }

    /* Add top/bottom margin to content to prevent overlap */
    #content {
        margin-top: 60px !important;
        margin-bottom: 60px !important;
    }

    /* Hide print button */
    .no-print {
        display: none !important;
    }

    /* Force page breaks to avoid cutting through text */
    h1, h2, h3 {
        page-break-after: avoid;
    }

    table, figure, img {
        page-break-inside: avoid;
    }
}

@media screen {
    /* On screen, show headers/footers for preview */
    .page-header, .page-footer {
        position: sticky;
    }
}
```

---

## API Design

### Backend Changes

#### Update Config Endpoint

**Modify**: `POST /api/config` in `main.py:101-168`

**Add Form Parameters**:
```python
@app.post("/api/config")
async def update_config(
    # ... existing 25 parameters ...

    # Page Headers (6 new fields)
    header_enabled: bool = Form(False),
    header_content: str = Form(""),
    header_alignment: str = Form("center"),
    header_font_size: str = Form("12px"),
    header_text_color: str = Form("#666666"),
    header_border_bottom: str = Form(""),

    # Page Footers (7 new fields)
    footer_enabled: bool = Form(False),
    footer_content: str = Form(""),
    footer_alignment: str = Form("center"),
    footer_font_size: str = Form("12px"),
    footer_text_color: str = Form("#666666"),
    footer_border_top: str = Form(""),
    footer_show_page_numbers: bool = Form(False),
):
    updates = {
        # ... existing config ...

        "page_headers": {
            "enabled": header_enabled,
            "content": header_content,
            "alignment": header_alignment,
            "font_size": header_font_size,
            "text_color": header_text_color,
            "border_bottom": header_border_bottom,
        },
        "page_footers": {
            "enabled": footer_enabled,
            "content": footer_content,
            "alignment": footer_alignment,
            "font_size": footer_font_size,
            "text_color": footer_text_color,
            "border_top": footer_border_top,
            "show_page_numbers": footer_show_page_numbers,
        }
    }

    pdf_gen.update_config(updates)
    return JSONResponse({"status": "success"})
```

---

#### Update Preview Route

**Modify**: `GET /preview/{file_id}` in `main.py:170-200`

**Add Header/Footer Processing**:
```python
@app.get("/preview/{file_id}")
async def preview(request: Request, file_id: str):
    # ... existing code to get markdown_content and filename ...

    # Process header content with template variables
    header_content = ""
    if config.get('page_headers', {}).get('enabled'):
        header_content = pdf_gen.apply_template_variables(
            content=config['page_headers']['content'],
            filename=filename,
            current_page=0,      # Placeholder (JS will replace)
            total_pages=0        # Placeholder (JS will replace)
        )

    # Process footer content with template variables
    footer_content = ""
    if config.get('page_footers', {}).get('enabled'):
        footer_content = config['page_footers']['content']

        # Auto-add page numbers if enabled
        if config['page_footers'].get('show_page_numbers'):
            if footer_content:
                footer_content += " - "
            footer_content += "Page {page} of {total_pages}"

        footer_content = pdf_gen.apply_template_variables(
            content=footer_content,
            filename=filename,
            current_page=0,
            total_pages=0
        )

    return templates.TemplateResponse(
        "preview.html",
        {
            "request": request,
            "filename": filename,
            "html_content": html_content,
            "codehilite_css": codehilite_css,
            "config": config,
            "header_content": header_content,    # NEW
            "footer_content": footer_content,    # NEW
        }
    )
```

---

## UI/UX Design

### Settings Form: Headers & Footers Section

Add after "Code Container" section in `templates/index.html`:

```html
<!-- Page Headers & Footers Section -->
<div class="mb-6 p-4 bg-white rounded-lg border border-gray-300">
    <h3 class="text-lg font-semibold mb-4">Page Headers & Footers</h3>

    <!-- Page Header -->
    <div class="mb-6">
        <div class="flex items-center mb-2">
            <input type="checkbox" id="header_enabled" name="header_enabled" class="mr-2">
            <label for="header_enabled" class="font-medium">Enable Header</label>
        </div>

        <div id="header-options" class="ml-6 space-y-3" style="display: none;">
            <!-- Content -->
            <div>
                <label class="block text-sm font-medium mb-1">
                    Header Content
                    <span class="text-xs text-gray-500 ml-2">
                        Use {page}, {total_pages}, {filename}, {date}
                    </span>
                </label>
                <input type="text" id="header_content" name="header_content"
                       class="w-full border rounded px-3 py-2"
                       placeholder="e.g., Document Title - {date}">
            </div>

            <!-- Alignment -->
            <div class="flex gap-4">
                <div class="flex-1">
                    <label class="block text-sm font-medium mb-1">Alignment</label>
                    <select id="header_alignment" name="header_alignment"
                            class="w-full border rounded px-3 py-2">
                        <option value="left">Left</option>
                        <option value="center" selected>Center</option>
                        <option value="right">Right</option>
                    </select>
                </div>

                <div class="flex-1">
                    <label class="block text-sm font-medium mb-1">Font Size</label>
                    <input type="text" id="header_font_size" name="header_font_size"
                           class="w-full border rounded px-3 py-2"
                           value="12px"
                           placeholder="e.g., 12px, 0.9rem">
                </div>
            </div>

            <!-- Colors & Border -->
            <div class="flex gap-4">
                <div class="flex-1">
                    <label class="block text-sm font-medium mb-1">Text Color</label>
                    <input type="text" id="header_text_color" name="header_text_color"
                           class="w-full border rounded px-3 py-2"
                           value="#666666"
                           placeholder="#666666">
                </div>

                <div class="flex-1">
                    <label class="block text-sm font-medium mb-1">
                        Border Bottom
                        <span class="text-xs text-gray-500 ml-1">(optional)</span>
                    </label>
                    <input type="text" id="header_border_bottom" name="header_border_bottom"
                           class="w-full border rounded px-3 py-2"
                           placeholder="e.g., 1px solid #ccc">
                </div>
            </div>
        </div>
    </div>

    <!-- Page Footer -->
    <div class="mb-4">
        <div class="flex items-center mb-2">
            <input type="checkbox" id="footer_enabled" name="footer_enabled" class="mr-2">
            <label for="footer_enabled" class="font-medium">Enable Footer</label>
        </div>

        <div id="footer-options" class="ml-6 space-y-3" style="display: none;">
            <!-- Content -->
            <div>
                <label class="block text-sm font-medium mb-1">
                    Footer Content
                    <span class="text-xs text-gray-500 ml-2">
                        Use {page}, {total_pages}, {filename}, {date}
                    </span>
                </label>
                <input type="text" id="footer_content" name="footer_content"
                       class="w-full border rounded px-3 py-2"
                       placeholder="e.g., Page {page} of {total_pages}">
            </div>

            <!-- Auto Page Numbers -->
            <div class="flex items-center">
                <input type="checkbox" id="footer_show_page_numbers" name="footer_show_page_numbers"
                       class="mr-2">
                <label for="footer_show_page_numbers" class="text-sm">
                    Automatically add "Page X of Y" to footer
                </label>
            </div>

            <!-- Alignment -->
            <div class="flex gap-4">
                <div class="flex-1">
                    <label class="block text-sm font-medium mb-1">Alignment</label>
                    <select id="footer_alignment" name="footer_alignment"
                            class="w-full border rounded px-3 py-2">
                        <option value="left">Left</option>
                        <option value="center" selected>Center</option>
                        <option value="right">Right</option>
                    </select>
                </div>

                <div class="flex-1">
                    <label class="block text-sm font-medium mb-1">Font Size</label>
                    <input type="text" id="footer_font_size" name="footer_font_size"
                           class="w-full border rounded px-3 py-2"
                           value="12px"
                           placeholder="e.g., 12px, 0.9rem">
                </div>
            </div>

            <!-- Colors & Border -->
            <div class="flex gap-4">
                <div class="flex-1">
                    <label class="block text-sm font-medium mb-1">Text Color</label>
                    <input type="text" id="footer_text_color" name="footer_text_color"
                           class="w-full border rounded px-3 py-2"
                           value="#666666"
                           placeholder="#666666">
                </div>

                <div class="flex-1">
                    <label class="block text-sm font-medium mb-1">
                        Border Top
                        <span class="text-xs text-gray-500 ml-1">(optional)</span>
                    </label>
                    <input type="text" id="footer_border_top" name="footer_border_top"
                           class="w-full border rounded px-3 py-2"
                           placeholder="e.g., 1px solid #ccc">
                </div>
            </div>
        </div>
    </div>

    <!-- Help Text -->
    <div class="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm">
        <strong>Template Variables:</strong>
        <ul class="list-disc list-inside mt-1 text-xs">
            <li><code>{page}</code> - Current page number</li>
            <li><code>{total_pages}</code> - Total number of pages</li>
            <li><code>{filename}</code> - Original filename</li>
            <li><code>{date}</code> - Current date (YYYY-MM-DD)</li>
            <li><code>{time}</code> - Current time (HH:MM)</li>
        </ul>
    </div>
</div>
```

---

### JavaScript: Toggle Options Visibility

```javascript
// Show/hide header options when checkbox is toggled
document.getElementById('header_enabled').addEventListener('change', (e) => {
    const options = document.getElementById('header-options');
    options.style.display = e.target.checked ? 'block' : 'none';
});

// Show/hide footer options when checkbox is toggled
document.getElementById('footer_enabled').addEventListener('change', (e) => {
    const options = document.getElementById('footer-options');
    options.style.display = e.target.checked ? 'block' : 'none';
});

// Initialize visibility on page load
if (document.getElementById('header_enabled').checked) {
    document.getElementById('header-options').style.display = 'block';
}
if (document.getElementById('footer_enabled').checked) {
    document.getElementById('footer-options').style.display = 'block';
}

// Add header/footer fields to change tracking
const fieldNames = [
    // ... existing 25 fields ...
    'header_enabled', 'header_content', 'header_alignment',
    'header_font_size', 'header_text_color', 'header_border_bottom',
    'footer_enabled', 'footer_content', 'footer_alignment',
    'footer_font_size', 'footer_text_color', 'footer_border_top',
    'footer_show_page_numbers'
];

// Total tracked fields: 25 (existing) + 13 (headers/footers) = 38 fields
```

---

## Implementation Roadmap

### Phase 1: Backend Configuration (1.5 hours)

**Task 1.1**: Add config schema to `pdf_generator.py`
- Add `page_headers` and `page_footers` to `get_default_config()`
- **Files**: `pdf_generator.py:44-87`

**Task 1.2**: Implement template variable replacement
- Add `apply_template_variables()` method
- Handle all 6 template variables
- **Files**: `pdf_generator.py` (new method, ~30 lines)

**Task 1.3**: Update config loading/saving
- Ensure backwards compatibility (existing configs without headers/footers)
- Add migration logic in `load_config()`
- **Files**: `pdf_generator.py:116-148`

**Task 1.4**: Update factory reset
- Include default header/footer config
- **Files**: `pdf_generator.py:44-87`

---

### Phase 2: API Routes (1 hour)

**Task 2.1**: Update config save endpoint
- Add 13 new form parameters for headers/footers
- Update config dict construction
- **Files**: `main.py:101-168`

**Task 2.2**: Update preview route
- Process header content with template variables
- Process footer content with template variables
- Handle auto page numbering option
- Pass header/footer content to template
- **Files**: `main.py:170-200`

---

### Phase 3: Frontend UI (2-2.5 hours)

**Task 3.1**: Add headers/footers section to settings form
- Header enable checkbox + options
- Footer enable checkbox + options
- Template variable help text
- **Files**: `templates/index.html` (+150 lines)

**Task 3.2**: Implement toggle visibility JavaScript
- Show/hide options based on checkbox state
- **Files**: `templates/index.html` (JavaScript section, +20 lines)

**Task 3.3**: Update field tracking
- Add 13 new fields to `fieldNames` array
- Update unsaved changes detection
- **Files**: `templates/index.html` (JavaScript, +1 line to array)

**Task 3.4**: Update form submission
- Ensure all header/footer fields are included in form data
- **Files**: `templates/index.html` (no changes needed if using FormData)

---

### Phase 4: Template Rendering (1-1.5 hours)

**Task 4.1**: Update preview.html structure
- Add header div (conditional)
- Add footer div (conditional)
- Adjust content margins
- **Files**: `templates/preview.html:100-120`

**Task 4.2**: Add print media queries
- Fixed positioning for print
- Page break handling
- Header/footer visibility
- **Files**: `templates/preview.html:30-80` (CSS section)

**Task 4.3**: Add page counter JavaScript (optional MVP feature)
- Calculate total pages
- Replace {page} and {total_pages} placeholders
- **Files**: `templates/preview.html` (JavaScript section, +20 lines)
- **Note**: This is approximate - true page numbering requires server-side PDF generation

---

### Phase 5: Testing & Polish (1 hour)

**Task 5.1**: Manual testing checklist
- [ ] Enable header with text - verify appears on all pages
- [ ] Enable footer with text - verify appears on all pages
- [ ] Test template variables ({filename}, {date}, {time})
- [ ] Test page numbering ({page}, {total_pages})
- [ ] Test alignment options (left, center, right)
- [ ] Test font size and color customization
- [ ] Test border styling
- [ ] Test with long content (multi-page)
- [ ] Test with short content (single page)
- [ ] Print to PDF and verify headers/footers appear

**Task 5.2**: Cross-browser testing
- [ ] Chrome (primary target)
- [ ] Safari
- [ ] Firefox
- [ ] Edge

**Task 5.3**: Edge cases
- [ ] Very long header text (test wrapping)
- [ ] Special characters in header/footer
- [ ] Empty header/footer content
- [ ] Both header and footer disabled
- [ ] Template variables in unsupported contexts

**Task 5.4**: Documentation
- Update `CLAUDE.md` with headers/footers overview
- Document template variables
- Add browser compatibility notes

---

## Testing Strategy

### Manual Testing Scenarios

#### Scenario 1: Academic Paper Format
**Config**:
- Header enabled: `Climate Change Research - {date}`
- Footer enabled: `Page {page} of {total_pages}`
- Alignment: center

**Expected**:
- Header appears at top of every page with date
- Footer shows page numbers at bottom
- Content doesn't overlap header/footer

#### Scenario 2: Corporate Letterhead
**Config**:
- Header enabled: `Acme Corporation`
- Footer enabled: `Confidential - Internal Use Only`
- Header border bottom: `2px solid #333`
- Footer border top: `1px solid #ccc`

**Expected**:
- Header with bottom border
- Footer with top border
- Professional appearance

#### Scenario 3: File Tracking
**Config**:
- Header disabled
- Footer enabled: `{filename} - Generated {datetime}`

**Expected**:
- No header
- Footer shows filename and generation timestamp

#### Scenario 4: Auto Page Numbering
**Config**:
- Header disabled
- Footer enabled: (empty content)
- Show page numbers: checked

**Expected**:
- Footer shows "Page X of Y" automatically

#### Scenario 5: Multi-Page Document
**Test**:
- Upload 10-page markdown document
- Enable header and footer
- Print to PDF

**Verify**:
- Headers appear on all 10 pages
- Footers appear on all 10 pages
- Page numbers increment correctly
- No content cutoff or overlap

---

### Browser Compatibility Testing

| Browser | Fixed Position | Print Media Queries | Page Counters | Status |
|---------|---------------|---------------------|---------------|--------|
| Chrome 100+ | ✅ | ✅ | ⚠️ Approximate | Fully Supported |
| Safari 15+ | ✅ | ✅ | ⚠️ Approximate | Fully Supported |
| Firefox 100+ | ✅ | ✅ | ⚠️ Approximate | Fully Supported |
| Edge 100+ | ✅ | ✅ | ⚠️ Approximate | Fully Supported |

**Note**: Page counters `{page}` and `{total_pages}` are approximate in browser-based printing. True page numbers require server-side PDF generation (future enhancement).

---

## Risk Assessment & Mitigation

### Risk 1: Page Number Accuracy
**Risk**: Browser-based page counting is approximate and unreliable
**Likelihood**: High
**Impact**: Medium (page numbers may be off by 1-2 pages)
**Mitigation**:
- Document limitation clearly in UI
- Add disclaimer near page number option
- Consider adding "approximate" text to page numbers
- Future: Migrate to server-side PDF generation (weasyprint, pdfkit)

**User-facing message**:
> "Note: Page numbers are approximate when using browser-based PDF generation. For precise page numbering, consider using server-side PDF generation."

---

### Risk 2: Content Overlap
**Risk**: Headers/footers may overlap with document content on some page breaks
**Likelihood**: Medium
**Impact**: Medium (text becomes unreadable)
**Mitigation**:
- Add sufficient top/bottom margins to content container
- Use `page-break-inside: avoid` on key elements
- Test with various content types (tables, code blocks, images)
- Provide option to adjust header/footer padding

---

### Risk 3: Long Header/Footer Text
**Risk**: Very long text in headers/footers may wrap awkwardly or overflow
**Likelihood**: Low (users typically use short text)
**Impact**: Low (cosmetic issue)
**Mitigation**:
- Add character limit suggestion (e.g., "Keep under 100 characters")
- Use `text-overflow: ellipsis` for long text
- Test with various text lengths

---

### Risk 4: Special Characters & HTML Injection
**Risk**: Users enter HTML/JavaScript in header/footer content
**Likelihood**: Low (most users enter plain text)
**Impact**: High (XSS vulnerability if not sanitized)
**Mitigation**:
- **Always escape user input** before rendering in template
- Use Jinja2's `| e` filter (escape) instead of `| safe`
- Validate template variables server-side
- **CRITICAL FIX**:

```html
<!-- INSECURE (current) -->
<div class="page-header">{{ header_content | safe }}</div>

<!-- SECURE (required) -->
<div class="page-header">{{ header_content | e }}</div>
```

---

### Risk 5: Browser Print Dialog Customization
**Risk**: Some browsers may add their own headers/footers in print dialog, conflicting with custom ones
**Likelihood**: Medium (varies by browser and user settings)
**Impact**: Low (cosmetic duplication)
**Mitigation**:
- Document that users should disable browser headers/footers in print dialog
- Add instruction in UI: "In print dialog, set Headers & Footers to 'None'"

---

## Dependencies & Prerequisites

### Required
- Python 3.8+ (already required)
- Jinja2 (already installed)
- FastAPI (already installed)

### Optional
- None for MVP

### System Requirements
- Modern browser with print-to-PDF support (Chrome, Safari, Firefox, Edge)

---

## Future Enhancements (Post-MVP)

### V2 Features
1. **Image Support**: Allow logo images in headers/footers
2. **First Page Different**: Different header/footer for page 1 vs rest
3. **Odd/Even Pages**: Different headers/footers for odd/even pages (book-style)
4. **Section-Specific**: Headers/footers that change per markdown section
5. **Server-Side PDF Generation**: Use weasyprint/pdfkit for accurate page numbers
6. **Rich Text Formatting**: Bold, italic, color within header/footer text
7. **Multiple Lines**: Support multi-line headers/footers
8. **Predefined Templates**: Gallery of header/footer presets

### Integration Ideas
- **Preset Integration**: Save header/footer config in presets (Feature 1)
- **Dynamic Content**: Pull header text from markdown frontmatter
- **Watermarks**: Add diagonal "DRAFT" or "CONFIDENTIAL" watermark

---

## Success Metrics (Post-Launch)

**Adoption Metrics**:
- % of users who enable headers (target: 40%)
- % of users who enable footers (target: 50%)
- % of users using page numbering (target: 70% of footer users)

**Usage Metrics**:
- Most common template variables used
- Average header/footer text length
- Browser breakdown of header/footer users

**Quality Metrics**:
- Header/footer rendering errors reported (target: <2%)
- Browser compatibility issues (target: <5%)

---

## Appendix: CSS Implementation Details

### Fixed Positioning for Print

```css
@media print {
    .page-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 40px; /* Adjust based on padding + font size */
        z-index: 1000;
    }

    .page-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 40px; /* Adjust based on padding + font size */
        z-index: 1000;
    }

    /* Ensure content doesn't overlap */
    @page {
        margin-top: 60mm;    /* Header height + buffer */
        margin-bottom: 60mm; /* Footer height + buffer */
    }

    #content {
        margin-top: 60px;
        margin-bottom: 60px;
    }
}
```

### Preventing Page Breaks

```css
/* Avoid breaking these elements across pages */
h1, h2, h3, h4, h5, h6 {
    page-break-after: avoid;
    page-break-inside: avoid;
}

table, figure, pre, blockquote {
    page-break-inside: avoid;
}

img {
    page-break-inside: avoid;
    page-break-after: auto;
}

/* Keep list items together */
li {
    page-break-inside: avoid;
}
```

---

## File Locations Summary

```
Modified Files:
  pdf_generator.py          → +80 lines (config schema, template variables)
  main.py                   → +40 lines (form params, preview processing)
  templates/index.html      → +180 lines (UI + JavaScript)
  templates/preview.html    → +60 lines (header/footer rendering, CSS)

Total Estimated Changes:
  ~360 lines of code
  4 files modified
```

---

**Total Estimated Effort**: 5-6 hours
**Priority**: High
**Status**: Ready for implementation

---

## Important Security Note

**CRITICAL**: Always escape user-provided header/footer content to prevent XSS attacks.

**Correct Implementation**:
```html
<!-- In preview.html template -->
<div class="page-header">{{ header_content | e }}</div>
<div class="page-footer">{{ footer_content | e }}</div>
```

**NEVER use `| safe` filter for user-provided content unless it has been sanitized.**
