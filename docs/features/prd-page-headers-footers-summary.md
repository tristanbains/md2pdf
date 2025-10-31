# PRD: Custom Page Headers & Footers (Summary)

**Feature ID**: `FEAT-002`
**Status**: Planned
**Priority**: High
**Complexity**: High (5-6 hours)
**Risk Level**: Medium

**Full Specification**: See `prd-page-headers-footers-full.md` for complete implementation details

---

## Executive Summary

Add customizable headers and footers that appear on every page of generated PDFs. Users can define custom text with template variables (`{page}`, `{total_pages}`, `{filename}`, `{date}`), configure styling and alignment, and enable automatic page numbering. Implementation uses HTML structure injection with fixed positioning for maximum browser compatibility.

---

## Problem Statement

### Current Limitations
- No way to add branding, titles, or identification to PDFs
- Page numbers must be manually added to markdown content
- Cannot add consistent headers/footers across all pages
- Professional documents require letterhead-style formatting

### User Pain Points
1. **Professional Documents**: Legal, academic, and business documents need headers/footers
2. **Page Navigation**: Readers need page numbers for reference
3. **Document Identification**: No easy way to add title, date, or version info
4. **Branding**: Companies need logos or company names on PDFs
5. **Manual Workarounds**: Users must edit markdown (doesn't work for multi-page)

---

## Goals & Success Metrics

### Primary Goals
1. Enable users to add custom text headers and footers to all pages
2. Support dynamic content (page numbers, filename, date)
3. Provide styling controls (alignment, font size, colors)
4. Maintain print quality and pagination

### Success Metrics
- 50%+ of users enable headers or footers
- Page numbering is most-used template variable (80% of users)
- Zero pagination issues reported
- Headers/footers display consistently across browsers

### Non-Goals (Out of Scope)
- Images in headers/footers (text only for MVP)
- Different headers for first page vs subsequent pages
- Different headers for odd/even pages
- Section-specific headers

---

## User Stories (Condensed)

### Story 1: Academic Paper
Add page numbers and paper title to every page for journal formatting requirements.
**Example**: Header: "Climate Change Study - Jan 2025", Footer: "Page {page} of {total_pages}"

### Story 2: Company Report
Add company name header and confidentiality footer for branding and security.
**Example**: Header: "Acme Corp - Quarterly Report", Footer: "Confidential - Internal Use Only"

### Story 3: Technical Documentation
Add filename and date to footer for tracking and versioning printed docs.
**Example**: Footer: "{filename} - Generated on {date}"

### Story 4: Corporate Intranet
Publish docs to internal network with consistent formatting and page numbers.

---

## Technical Architecture (High-Level)

### Implementation Approach
**HTML Structure Injection** (NOT CSS `@page`)

**Rationale**:
- CSS `@page` support inconsistent across browsers
- `@page` doesn't reliably support dynamic content
- HTML fixed positioning works universally via `window.print()`
- More control over styling and positioning

### Template Variables Supported

| Variable | Description | Example Output |
|----------|-------------|----------------|
| `{page}` | Current page number | `1`, `2`, `3` |
| `{total_pages}` | Total pages | `10` |
| `{filename}` | Original filename | `report.md` |
| `{date}` | Current date (ISO) | `2025-01-15` |
| `{time}` | Current time (24h) | `14:30` |
| `{datetime}` | Date and time | `2025-01-15 14:30` |

**Example Usage**:
- `"Page {page} of {total_pages}"` → "Page 2 of 10"
- `"{filename} - Generated on {date}"` → "report.md - Generated on 2025-01-15"

### Configuration Schema

Added to `pdf_generator.py:get_default_config()`:

```python
'page_headers': {
    'enabled': False,
    'content': '',              # Plain text with template variables
    'alignment': 'center',      # 'left', 'center', 'right'
    'font_size': '12px',
    'text_color': '#666666',
    'border_bottom': '',        # Optional CSS border
},
'page_footers': {
    'enabled': False,
    'content': '',
    'alignment': 'center',
    'font_size': '12px',
    'text_color': '#666666',
    'border_top': '',
    'show_page_numbers': False, # Auto-add "Page X of Y"
}
```

---

## API Changes

### Update Config Endpoint
**Route**: `POST /api/config`
**New Parameters**: 13 fields (6 for headers, 7 for footers)

### Update Preview Route
**Route**: `GET /preview/{file_id}`
**Changes**:
- Process header/footer content with template variables
- Pass processed content to template
- Handle auto page numbering option

---

## UI Components

### Settings Form: Headers & Footers Section
**Location**: After "Code Container" section

**Components**:
- Header enable checkbox with collapsible options
  - Content input (with template variable help text)
  - Alignment dropdown (left/center/right)
  - Font size input
  - Text color input
  - Border bottom input
- Footer enable checkbox with collapsible options
  - Content input
  - Auto page numbers checkbox
  - Alignment dropdown
  - Font size input
  - Text color input
  - Border top input
- Template variables help box

### Preview Page Updates
**HTML Structure**:
- Fixed header div at top (conditional)
- Fixed footer div at bottom (conditional)
- Content with adjusted margins to prevent overlap

**Print Media Queries**:
- Fixed positioning for headers/footers in print mode
- Page break handling (avoid breaking headers/tables)
- Content margin adjustments

---

## Implementation Roadmap

### Phase 1: Backend Configuration (1.5 hours)
1. Add config schema to `pdf_generator.py`
2. Implement `apply_template_variables()` method
3. Update config loading/saving with backwards compatibility
4. Update factory reset

**Files**: `pdf_generator.py` (~80 lines)

### Phase 2: API Routes (1 hour)
1. Update config save endpoint with 13 new form parameters
2. Update preview route to process header/footer content
3. Handle template variables and auto page numbering

**Files**: `main.py` (~40 lines)

### Phase 3: Frontend UI (2-2.5 hours)
1. Add headers/footers section to settings form
2. Implement toggle visibility JavaScript
3. Update field tracking (add 13 new fields)
4. Ensure form submission includes all fields

**Files**: `templates/index.html` (~180 lines)

### Phase 4: Template Rendering (1-1.5 hours)
1. Update `preview.html` structure (header/footer divs, margins)
2. Add print media queries (fixed positioning, page breaks)
3. Add page counter JavaScript (optional - approximate only)

**Files**: `templates/preview.html` (~60 lines)

### Phase 5: Testing & Polish (1 hour)
- Manual testing (all template variables, alignment, styling)
- Cross-browser testing (Chrome, Safari, Firefox, Edge)
- Edge cases (long text, special characters, multi-page docs)
- Documentation updates

---

## Important Limitations

### Page Number Accuracy
**Limitation**: Browser-based page counting is **approximate and unreliable**

**Why**: JavaScript cannot accurately determine page breaks before printing. True page numbers require server-side PDF generation (e.g., weasyprint).

**Impact**: Page numbers may be off by 1-2 pages, especially with:
- Tables that span pages
- Large images
- Variable content heights

**Mitigation**:
- Document limitation clearly in UI
- Add disclaimer: "Note: Page numbers are approximate with browser-based PDF generation"
- Consider showing "~" prefix: "~Page 2 of ~10"
- Future: Migrate to server-side PDF generation for accurate numbering

---

## Risk Assessment

### Risk 1: Page Number Accuracy
**Likelihood**: High | **Impact**: Medium
**Mitigation**: Document limitation, add disclaimer, consider approximate prefix

### Risk 2: Content Overlap
**Likelihood**: Medium | **Impact**: Medium
**Mitigation**: Sufficient margins, page-break-inside CSS rules, testing

### Risk 3: Long Header/Footer Text
**Likelihood**: Low | **Impact**: Low
**Mitigation**: Character limit suggestion, text-overflow ellipsis

### Risk 4: XSS Vulnerability
**Likelihood**: Low | **Impact**: High
**Mitigation**: **CRITICAL** - Use `{{ content | e }}` NOT `{{ content | safe }}`

### Risk 5: Browser Print Dialog Conflicts
**Likelihood**: Medium | **Impact**: Low
**Mitigation**: Document that users should disable browser headers/footers in print dialog

---

## Security Note

**CRITICAL**: Always escape user-provided header/footer content to prevent XSS attacks.

**Correct Implementation**:
```html
<!-- SECURE (required) -->
<div class="page-header">{{ header_content | e }}</div>
<div class="page-footer">{{ footer_content | e }}</div>
```

**NEVER use `| safe` filter for user-provided content unless sanitized.**

---

## Testing Checklist (Quick Reference)

**Core Functions**:
- [ ] Enable header with text - appears on all pages
- [ ] Enable footer with text - appears on all pages
- [ ] Template variables work ({filename}, {date}, {time})
- [ ] Page numbering works ({page}, {total_pages})
- [ ] Alignment options (left, center, right)
- [ ] Font size and color customization
- [ ] Border styling
- [ ] Multi-page documents (10+ pages)
- [ ] Print to PDF verification

**Cross-Browser**:
- [ ] Chrome, Safari, Firefox, Edge compatibility

**Edge Cases**:
- [ ] Very long header text (wrapping)
- [ ] Special characters in header/footer
- [ ] Empty header/footer content
- [ ] Both disabled
- [ ] Template variables with missing data

---

## Dependencies & Prerequisites

### Required
- Python 3.8+ ✓ (already required)
- Jinja2 ✓ (already installed)
- FastAPI ✓ (already installed)

### System Requirements
- Modern browser with print-to-PDF support

---

## Future Enhancements (Post-MVP)

**V2 Features**:
- Image support (logos in headers/footers)
- First page different (unique header/footer for page 1)
- Odd/even pages (book-style formatting)
- Section-specific headers (change per markdown section)
- **Server-side PDF generation** for accurate page numbers
- Rich text formatting (bold, italic, colors)
- Multi-line headers/footers
- Predefined header/footer templates

**Integration Ideas**:
- Save header/footer config in presets (FEAT-001 integration)
- Pull header text from markdown frontmatter
- Diagonal watermarks ("DRAFT", "CONFIDENTIAL")

---

## Success Metrics (Post-Launch)

**Adoption**:
- 40%+ enable headers
- 50%+ enable footers
- 70% of footer users use page numbering

**Usage**:
- Most common template variables
- Average header/footer text length
- Browser breakdown

**Quality**:
- <2% rendering errors
- <5% browser compatibility issues

---

## Quick File Reference

```
Modified Files:
  pdf_generator.py          +80 lines
  main.py                   +40 lines
  templates/index.html      +180 lines
  templates/preview.html    +60 lines

Total: ~360 lines of code, 4 files modified
```

---

**Total Estimated Effort**: 5-6 hours
**Implementation Difficulty**: High (due to print layout complexity)
**User Impact**: High (professional document formatting)

For detailed code examples, HTML templates, CSS media queries, and JavaScript implementations, see **`prd-page-headers-footers-full.md`**.
