# PRD: Standalone HTML Export with Embedded CSS (Summary)

**Feature ID**: `FEAT-003`
**Status**: Planned
**Priority**: Medium-High
**Complexity**: Medium-High (4-5 hours)
**Risk Level**: Medium

**Full Specification**: See `prd-standalone-html-export-full.md` for complete implementation details

---

## Executive Summary

Add the ability to export markdown documents as standalone, self-contained HTML files with all CSS embedded. Files work offline without CDN dependencies and are optimized for minimal file size (~20-30KB vs 300KB+ with CDN). Implementation uses TailwindCSS Standalone CLI with caching for optimal performance and no Node.js dependency.

---

## Problem Statement

### Current Limitations
- Preview HTML requires internet connection (TailwindCSS CDN)
- Cannot save fully self-contained HTML files
- CDN-dependent HTML breaks when offline
- File sharing requires both HTML + network access
- Large bandwidth usage (~300KB TailwindCSS load per view)

### User Pain Points
1. **Offline Access**: Cannot view generated HTML without internet
2. **Archival**: Saved HTML files break months later if CDN changes
3. **Sharing**: Recipients need internet to view shared HTML files
4. **Performance**: 300KB CDN load on every page view
5. **Portability**: Cannot email/share HTML files as standalone documents

---

## Goals & Success Metrics

### Primary Goals
1. Generate standalone HTML files with embedded CSS (no external dependencies)
2. Achieve 85%+ file size reduction vs CDN version (20-30KB vs 300KB)
3. Maintain identical visual appearance to preview
4. Work offline and indefinitely without CDN access
5. No Node.js dependency (Python-first approach)

### Success Metrics
- 90%+ of generated HTML files work offline
- File size <30KB for typical documents
- CSS generation time <200ms with caching
- Zero visual regressions vs preview
- 30%+ of users utilize standalone HTML export

### Non-Goals (Out of Scope)
- Inline images as base64 (keep image URLs as-is)
- JavaScript interactivity (static HTML only)
- Responsive mobile styling (optimized for PDF/print)
- Multiple output formats (HTML only)

---

## User Stories (Condensed)

### Story 1: Offline Documentation
Save documentation as standalone HTML for viewing on planes or restricted networks.

### Story 2: Email Sharing
Email HTML reports to clients (<50KB, email-friendly size) without requiring special software.

### Story 3: Archival Storage
Preserve documents as self-contained HTML viewable decades later without CDN dependencies.

### Story 4: Corporate Intranet
Publish HTML docs to internal intranet, accessible on air-gapped networks without external CDN.

---

## Technical Architecture (High-Level)

### Implementation Approach
**TailwindCSS Standalone CLI with Caching**

**Why This Approach**:
- No Node.js/npm required (Python-first philosophy)
- Official TailwindCSS tool (maintained by Tailwind Labs)
- True CSS purging (5-20KB output vs 300KB CDN)
- Supports typography plugin
- Can be called from Python via subprocess
- Caching makes it performant (~1ms after first generation)

**Alternatives Rejected**:
- CDN with disclaimer: Still requires internet
- PostCSS + PurgeCSS: Requires Node.js ecosystem
- Pre-generated templates: Less flexible

### File Size Comparison

| Content Type | CDN Version | Standalone Version | Reduction |
|--------------|-------------|--------------------|-----------|
| Small doc (5KB) | 310KB | 18KB | 94% |
| Medium doc (20KB) | 330KB | 25KB | 92% |
| Large doc (100KB) | 420KB | 135KB | 68% |
| Complex styles | 315KB | 28KB | 91% |

**Target**: 85%+ reduction for typical documents

---

## Binary Management

### TailwindCSS CLI Binaries
**Download** (one-time setup via Makefile):
```bash
make install-tailwind
```

**Binaries Stored**:
```
bin/
├── tailwindcss-macos       # macOS ARM64/x86
├── tailwindcss-linux       # Linux x64
└── tailwindcss-windows.exe # Windows x64
```

**Detection**: Automatic platform detection (macOS, Linux, Windows)

**Version**: v3.4+ (for typography plugin support)

---

## Configuration Files

**File 1**: `tailwind.config.js` (project root)
- Configures typography plugin
- Content specified via CLI flag

**File 2**: `static/input.css`
- TailwindCSS source (@tailwind base/components/utilities)

---

## CSS Generation Pipeline

### High-Level Flow
1. **Convert markdown to HTML** (existing pipeline)
2. **Build full HTML document** with TailwindCSS classes
3. **Generate cache key** from HTML content + config (MD5 hash)
4. **Check cache** - return cached CSS if available (1ms)
5. **Write HTML to temp file** for CLI scanning
6. **Execute Tailwind CLI** with purging (100-200ms first run)
7. **Cache generated CSS** for future use
8. **Combine HTML + embedded CSS** into final document
9. **Fallback to CDN** if generation fails

### Key Methods (PDFGenerator)
- `_get_tailwind_cli_path()` - Platform detection
- `generate_tailwind_css(html_content)` - CSS generation with caching
- `generate_standalone_html(markdown, filename)` - Complete HTML builder
- `_generate_cdn_fallback_html()` - Fallback for failures

---

## API Design

### New Export Endpoint
**Route**: `GET /export/{file_id}/html`

**Behavior**:
1. Load markdown content and filename
2. Check for temp config (unsaved settings)
3. Generate standalone HTML with embedded CSS
4. Return as downloadable file (`{filename}.html`)
5. Fallback to CDN HTML if CSS generation fails

**Response**:
- Content-Type: `text/html`
- Content-Disposition: `attachment; filename="{name}.html"`

---

## UI Components

### Preview Page: Export Button
**Location**: Alongside existing "Print/Save as PDF" button

**Components**:
- "Download Standalone HTML" button (green)
- JavaScript export function
- Optional status indicator ("Generating...")

**Behavior**:
- Click button → triggers `/export/{file_id}/html`
- Downloads HTML file to user's device
- Works with temp configs (unsaved settings)

---

## Implementation Roadmap

### Phase 1: Setup & Binary Management (30 min)
1. Create Makefile target: `make install-tailwind`
2. Create `tailwind.config.js` and `static/input.css`
3. Update `.gitignore` (bin/, css_cache/)

**Files**: `Makefile` (+10 lines), new config files

### Phase 2: CSS Generation Implementation (1.5-2 hours)
1. Add CLI path detection (`_get_tailwind_cli_path()`)
2. Implement CSS generation with caching
3. Add cache directory management
4. Error handling and CDN fallback

**Files**: `pdf_generator.py` (+250 lines)

### Phase 3: Standalone HTML Generation (1 hour)
1. Implement standalone HTML builder
2. Implement CDN fallback method
3. Template variable support (if FEAT-002 exists)

**Files**: `pdf_generator.py` (+100 lines)

### Phase 4: API Routes (30 min)
1. Add export HTML endpoint
2. Load markdown, generate HTML, return as download

**Files**: `main.py` (+35 lines)

### Phase 5: Frontend UI (30 min)
1. Add export button to preview page
2. Add export JavaScript function
3. Optional status indicator

**Files**: `templates/preview.html` (+25 lines)

### Phase 6: Testing & Optimization (1 hour)
- Manual testing (offline functionality, file size, caching)
- Performance testing (generation time, cache hit rate)
- Cross-platform testing (macOS, Linux, Windows)
- Edge cases (large docs, many classes, CLI not installed)

---

## Performance Benchmarks

| Operation | Target | Acceptable | Unacceptable |
|-----------|--------|------------|--------------|
| CSS generation (first run) | <100ms | <200ms | >500ms |
| CSS generation (cached) | <1ms | <5ms | >10ms |
| Full HTML export | <300ms | <500ms | >1s |
| Cache lookup | <1ms | <5ms | >10ms |

---

## Testing Checklist (Quick Reference)

**Core Functions**:
- [ ] Download Tailwind CLI binaries
- [ ] Generate standalone HTML
- [ ] Verify HTML works offline (disable network)
- [ ] Check file size (<30KB typical)
- [ ] Test caching (second export <1ms)

**Offline Testing**:
1. Generate and download HTML
2. Disconnect from internet
3. Open HTML in browser
4. Verify: styling intact, no console errors, no broken CDN links

**Cross-Platform**:
- [ ] macOS ARM64 and x86_64
- [ ] Linux x64
- [ ] Windows (if applicable)

**Edge Cases**:
- [ ] Very large markdown (>100KB)
- [ ] Many custom classes (>50)
- [ ] Tailwind CLI not installed (CDN fallback)
- [ ] Cache directory cleanup

---

## Risk Assessment

### Risk 1: Tailwind CLI Binary Not Installed
**Likelihood**: Medium | **Impact**: High
**Mitigation**:
- Fallback to CDN-based HTML if binary missing
- Show clear error with installation instructions
- Document binary installation in README

### Risk 2: CSS Generation Timeout
**Likelihood**: Low | **Impact**: Medium
**Mitigation**:
- 10 second timeout on subprocess
- Fallback to CDN HTML on timeout
- Log timeout events

### Risk 3: Platform Detection Failure
**Likelihood**: Low | **Impact**: High
**Mitigation**:
- Manual CLI path override in config
- `TAILWIND_CLI_PATH` environment variable support
- Fallback to CDN if detection fails

### Risk 4: Cache Directory Growth
**Likelihood**: Medium | **Impact**: Low
**Mitigation**:
- LRU cache eviction (keep 100 most recent)
- Cache size limit (50MB max)
- `make clean-css-cache` command
- Document cache location

### Risk 5: Typography Plugin Missing
**Likelihood**: Very Low | **Impact**: High
**Mitigation**:
- Verify CLI version supports typography (v3.4+)
- Version check in installation script
- Document minimum required version

---

## Dependencies & Prerequisites

### Required
- Python 3.8+ ✓ (already required)
- Subprocess module ✓ (stdlib)
- Hashlib module ✓ (stdlib)

### System Requirements
- 50MB disk space for Tailwind CLI binaries
- 10-50MB for CSS cache (self-managing)
- Write access to `bin/` and `temp_uploads/css_cache/`

### External Dependencies
- TailwindCSS Standalone CLI v3.4+ (downloaded via Makefile)
- Internet connection for initial binary download
- **No runtime internet dependency** (works fully offline after setup)

---

## Future Enhancements (Post-MVP)

**V2 Features**:
- Inline images as base64 (truly self-contained)
- Additional CSS minification/gzip compression
- Export as EPUB, DOCX, PDF (server-side generation)
- Progressive loading for large docs
- Custom CSS injection
- Batch export (multiple markdown → ZIP)

**Optimization Ideas**:
- Pre-warming cache on startup
- Shared CSS cache (based on config only)
- Self-host Tailwind CSS as CDN fallback

---

## Success Metrics (Post-Launch)

**Adoption**:
- 30%+ of users export standalone HTML
- HTML export vs PDF export ratio 1:3
- 50% export HTML more than once

**Performance**:
- Average CSS generation <100ms first run
- Cache hit rate >80%
- File size reduction >85%

**Quality**:
- Export failure rate <2%
- Offline functionality rate >95%
- Visual regression <1% pixel diff

---

## Installation Instructions (User-Facing)

Add to README:

### Standalone HTML Export Setup

To enable standalone HTML export with optimized CSS:

1. **Download Tailwind CLI** (one-time setup):
   ```bash
   make install-tailwind
   ```

2. **Verify installation**:
   ```bash
   ls -lh bin/tailwindcss-*
   ```

3. **Usage**:
   - Upload markdown and generate preview
   - Click "Download Standalone HTML" button
   - HTML file works offline with all styles embedded

**Note**: HTML export will fall back to CDN-based HTML if Tailwind CLI is not installed. Run `make install-tailwind` for best results (85%+ smaller files).

---

## Quick File Reference

```
New Files:
  bin/tailwindcss-macos       → Downloaded via Makefile
  bin/tailwindcss-linux       → Downloaded via Makefile
  tailwind.config.js          → New config file
  static/input.css            → TailwindCSS source

Modified Files:
  pdf_generator.py            +250 lines
  main.py                     +35 lines
  templates/preview.html      +25 lines
  Makefile                    +10 lines
  .gitignore                  +2 lines

Generated Files:
  temp_uploads/css_cache/     → CSS cache directory
    {hash}.css                → Cached purged CSS files
```

---

**Total Estimated Effort**: 4-5 hours
**Implementation Difficulty**: Medium-High (subprocess management, caching)
**User Impact**: High (offline access, email-friendly file sharing)

For detailed code examples, subprocess handling, error scenarios, and alternative implementations, see **`prd-standalone-html-export-full.md`**.
