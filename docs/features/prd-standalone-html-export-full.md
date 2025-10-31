# PRD: Standalone HTML Export with Embedded CSS

**Feature ID**: `FEAT-003`
**Status**: Planned
**Priority**: Medium-High
**Complexity**: Medium-High (4-5 hours)
**Risk Level**: Medium

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

## User Stories & Use Cases

### User Story 1: Offline Documentation
**As a** software developer
**I want to** save documentation as standalone HTML
**So that** I can view it offline on planes or restricted networks

**Acceptance Criteria**:
- Can download HTML file from preview page
- HTML opens in browser without internet
- All styling intact (no broken CDN links)

### User Story 2: Email Sharing
**As a** report writer
**I want to** email HTML reports to clients
**So that** they can view reports without special software or internet

**Acceptance Criteria**:
- HTML file <50KB (email-friendly size)
- Recipients can open in any browser
- No external dependencies

### User Story 3: Archival Storage
**As an** archivist
**I want to** preserve documents as self-contained HTML
**So that** they remain viewable decades later without CDN dependencies

**Acceptance Criteria**:
- HTML files contain all necessary CSS
- No reliance on external URLs
- Files remain functional after years

### User Story 4: Corporate Intranet
**As a** corporate user
**I want to** publish HTML docs to internal intranet
**So that** employees can access docs on restricted networks without external CDN access

**Acceptance Criteria**:
- HTML works on air-gapped networks
- No security warnings about external resources
- Fast load times

---

## Technical Specifications

### Architecture Overview

**Approach**: TailwindCSS Standalone CLI with caching

**Rationale** (from research):
- No Node.js/npm required (Python-first philosophy)
- Official TailwindCSS tool (maintained by Tailwind Labs)
- True CSS purging (5-20KB output vs 300KB CDN)
- Supports typography plugin
- Can be called from Python via subprocess
- Caching makes it performant (~1ms after first generation)

**Alternative Rejected**:
- **CDN with disclaimer**: Still requires internet (doesn't solve offline use case)
- **PostCSS + PurgeCSS**: Requires Node.js ecosystem (adds complexity)
- **Pre-generated templates**: Less flexible, doesn't adapt to custom classes

---

### TailwindCSS Standalone CLI Integration

#### Binary Management

**Download Binaries** (one-time setup):
```bash
# Create bin directory
mkdir -p /Users/tristanbains/Desktop/Projects/Windsurf/md2pdf/bin

# Download for macOS ARM64 (M1/M2)
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64
mv tailwindcss-macos-arm64 bin/tailwindcss-macos
chmod +x bin/tailwindcss-macos

# Download for Linux x64
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
mv tailwindcss-linux-x64 bin/tailwindcss-linux
chmod +x bin/tailwindcss-linux

# Download for Windows (if needed)
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-windows-x64.exe
mv tailwindcss-windows-x64.exe bin/tailwindcss-windows.exe
```

**Binary Version**: Use latest stable (v3.4+ recommended for typography plugin support)

**Storage**: `bin/` directory (gitignored, downloaded via Makefile command)

---

#### Configuration Files

**File 1**: `tailwind.config.js` (project root)
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [],  // Content specified via CLI --content flag
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
```

**Note**: Typography plugin must be configured, but the binary includes it by default.

---

**File 2**: `static/input.css` (TailwindCSS source)
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

#### CSS Generation Pipeline

**Python Implementation** (`pdf_generator.py`):

```python
import subprocess
import tempfile
import hashlib
import platform
from pathlib import Path

class PDFGenerator:
    def __init__(self, config_path: str = None):
        # ... existing code ...
        self.css_cache_dir = Path("temp_uploads/css_cache")
        self.css_cache_dir.mkdir(parents=True, exist_ok=True)
        self.tailwind_cli_path = self._get_tailwind_cli_path()

    def _get_tailwind_cli_path(self) -> str:
        """Detect platform and return appropriate Tailwind CLI binary path"""
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == 'darwin':
            if 'arm' in machine or machine == 'arm64':
                return 'bin/tailwindcss-macos'
            else:
                return 'bin/tailwindcss-macos'  # Intel uses same binary
        elif system == 'linux':
            return 'bin/tailwindcss-linux'
        elif system == 'windows':
            return 'bin/tailwindcss-windows.exe'
        else:
            raise RuntimeError(f"Unsupported platform: {system}")

    def generate_tailwind_css(self, html_content: str) -> str:
        """
        Generate purged TailwindCSS for HTML content with caching.

        Args:
            html_content: Full HTML with TailwindCSS classes applied

        Returns:
            Purged CSS string (5-20KB typical size)
        """
        # Create cache key from HTML content + config
        cache_key = hashlib.md5(
            (html_content + str(self.config)).encode()
        ).hexdigest()
        cache_file = self.css_cache_dir / f"{cache_key}.css"

        # Return cached CSS if available
        if cache_file.exists():
            return cache_file.read_text()

        # Check if Tailwind CLI binary exists
        if not Path(self.tailwind_cli_path).exists():
            raise FileNotFoundError(
                f"Tailwind CLI not found at {self.tailwind_cli_path}. "
                f"Run 'make install-tailwind' to download."
            )

        # Write HTML to temp file for CLI to scan
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.html', delete=False, encoding='utf-8'
        ) as f:
            f.write(html_content)
            html_path = f.name

        # Generate CSS using Tailwind CLI
        output_path = tempfile.mktemp(suffix='.css')

        try:
            result = subprocess.run([
                self.tailwind_cli_path,
                '-i', 'static/input.css',
                '-o', output_path,
                f'--content={html_path}',
                '--minify'
            ], check=True, capture_output=True, text=True, timeout=10)

            # Read generated CSS
            css = Path(output_path).read_text()

            # Cache for future use
            cache_file.write_text(css)

            # Cleanup temp files
            Path(html_path).unlink()
            Path(output_path).unlink()

            return css

        except subprocess.CalledProcessError as e:
            # Cleanup temp files
            if Path(html_path).exists():
                Path(html_path).unlink()
            if Path(output_path).exists():
                Path(output_path).unlink()

            raise RuntimeError(f"Tailwind CSS generation failed: {e.stderr}")

        except subprocess.TimeoutExpired:
            # Cleanup temp files
            if Path(html_path).exists():
                Path(html_path).unlink()

            raise RuntimeError("Tailwind CSS generation timed out (>10s)")

    def generate_standalone_html(
        self,
        markdown_content: str,
        filename: str = "document"
    ) -> str:
        """
        Generate complete standalone HTML with embedded CSS.

        Args:
            markdown_content: Raw markdown text
            filename: Original filename (for title and metadata)

        Returns:
            Complete HTML document with embedded CSS
        """
        # Step 1: Convert markdown to HTML (existing pipeline)
        html_body = self.markdown_to_html(markdown_content)
        html_body = self.apply_custom_classes(html_body)
        html_body = self.apply_codehilite_wrapper_styling(html_body)

        # Step 2: Get CodeHilite CSS for syntax highlighting
        codehilite_css = self.get_codehilite_css(
            self.config.get('codehilite_theme', 'default')
        )

        # Step 3: Build full HTML document for CSS scanning
        prose_size = self.config.get('prose_size', 'prose')
        prose_color = self.config.get('prose_color', '')

        # Create complete HTML structure
        full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{filename}</title>
</head>
<body>
    <article class="prose {prose_size} {prose_color}">
        {html_body}
    </article>
</body>
</html>'''

        # Step 4: Generate purged TailwindCSS
        try:
            tailwind_css = self.generate_tailwind_css(full_html)
        except Exception as e:
            # Fallback: return HTML with CDN link if CSS generation fails
            print(f"Warning: Tailwind CSS generation failed: {e}")
            return self._generate_cdn_fallback_html(
                html_body, filename, codehilite_css
            )

        # Step 5: Combine everything into final HTML
        standalone_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{filename}</title>

    <!-- Embedded TailwindCSS (purged) -->
    <style>
{tailwind_css}
    </style>

    <!-- Embedded CodeHilite CSS -->
    <style>
{codehilite_css}
    </style>

    <!-- Print-optimized styles -->
    <style>
        @media print {{
            @page {{
                size: A4 portrait;
                margin: 20mm;
            }}

            body {{
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
            }}

            .prose {{
                max-width: 100% !important;
            }}
        }}

        @media screen {{
            body {{
                max-width: 210mm;
                margin: 20px auto;
                padding: 20px;
                background: #f5f5f5;
            }}

            article {{
                background: white;
                padding: 40px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
        }}
    </style>
</head>
<body>
    <article class="prose {prose_size} {prose_color}">
{html_body}
    </article>
</body>
</html>'''

        return standalone_html

    def _generate_cdn_fallback_html(
        self,
        html_body: str,
        filename: str,
        codehilite_css: str
    ) -> str:
        """
        Generate HTML with CDN link as fallback if CSS generation fails.
        """
        prose_size = self.config.get('prose_size', 'prose')
        prose_color = self.config.get('prose_color', '')

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{filename}</title>

    <!-- Fallback to CDN (requires internet) -->
    <script src="https://cdn.tailwindcss.com?plugins=typography"></script>

    <style>
{codehilite_css}
    </style>

    <style>
        /* Print styles */
        @media print {{
            @page {{ size: A4 portrait; margin: 20mm; }}
            body {{ print-color-adjust: exact; }}
        }}
        @media screen {{
            body {{ max-width: 210mm; margin: 20px auto; padding: 20px; }}
        }}
    </style>
</head>
<body>
    <article class="prose {prose_size} {prose_color}">
{html_body}
    </article>
</body>
</html>'''
```

---

### API Design

#### New Export Endpoint

**Route**: `GET /export/{file_id}/html`

**Purpose**: Generate and download standalone HTML file

**Implementation** (`main.py`):
```python
from fastapi.responses import Response

@app.get("/export/{file_id}/html")
async def export_html(file_id: str):
    """
    Export markdown as standalone HTML with embedded CSS.

    Args:
        file_id: UUID of uploaded markdown file

    Returns:
        FileResponse with standalone HTML
    """
    # Get markdown content and filename
    markdown_content, original_filename = get_file_content(file_id)

    # Check for temp config
    temp_config_path = os.path.join(TEMP_UPLOAD_DIR, f"{file_id}.tempconfig")
    if os.path.exists(temp_config_path):
        with open(temp_config_path, 'r') as f:
            temp_config = json.load(f)
            pdf_gen.config = temp_config

    # Generate standalone HTML
    try:
        html = pdf_gen.generate_standalone_html(
            markdown_content,
            filename=original_filename
        )

        # Determine output filename
        html_filename = Path(original_filename).stem + ".html"

        # Return as downloadable file
        return Response(
            content=html,
            media_type="text/html",
            headers={
                "Content-Disposition": f'attachment; filename="{html_filename}"'
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"HTML generation failed: {str(e)}"}
        )
```

---

#### Optional: Export Current Config as HTML

**Route**: `POST /export/config/html`

**Purpose**: Export current config as standalone HTML (without uploading markdown)

Useful for testing CSS generation or exporting sample/template HTML.

---

## UI/UX Design

### Preview Page: Export Button

Add export button to `templates/preview.html` alongside existing "Print/Save as PDF" button:

```html
<!-- Print Controls -->
<div class="no-print mb-8 flex gap-4">
    <!-- Existing Print Button -->
    <button onclick="window.print()"
            class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
        🖨️ Print / Save as PDF
    </button>

    <!-- NEW: Export as HTML Button -->
    <button onclick="exportAsHTML()"
            class="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium">
        💾 Download Standalone HTML
    </button>

    <!-- Back Button -->
    <a href="/"
       class="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium">
        ← Back
    </a>
</div>

<script>
function exportAsHTML() {
    // Get file ID from URL (/preview/{file_id})
    const fileId = window.location.pathname.split('/').pop();

    // Trigger download
    window.location.href = `/export/${fileId}/html`;
}
</script>
```

---

### Status Indicator (Optional Enhancement)

Show CSS generation status while processing:

```html
<div id="export-status" class="hidden fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded shadow">
    Generating standalone HTML...
</div>

<script>
async function exportAsHTML() {
    const fileId = window.location.pathname.split('/').pop();
    const statusEl = document.getElementById('export-status');

    // Show status
    statusEl.classList.remove('hidden');

    try {
        // Trigger download
        window.location.href = `/export/${fileId}/html`;

        // Hide status after 2 seconds
        setTimeout(() => {
            statusEl.classList.add('hidden');
        }, 2000);
    } catch (error) {
        statusEl.textContent = 'Export failed';
        statusEl.classList.add('bg-red-600');
        setTimeout(() => {
            statusEl.classList.add('hidden');
        }, 3000);
    }
}
</script>
```

---

## Implementation Roadmap

### Phase 1: Setup & Binary Management (30 min)

**Task 1.1**: Create bin directory and download script
- Add Makefile target: `make install-tailwind`
- Download binaries for macOS, Linux, Windows
- **Files**: `Makefile` (+10 lines)

```makefile
# Download Tailwind CLI binaries
install-tailwind:
	@echo "📦 Downloading Tailwind CSS CLI..."
	@mkdir -p bin
	@curl -sL https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64 -o bin/tailwindcss-macos
	@chmod +x bin/tailwindcss-macos
	@curl -sL https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64 -o bin/tailwindcss-linux
	@chmod +x bin/tailwindcss-linux
	@echo "✅ Tailwind CLI installed!"
```

**Task 1.2**: Create configuration files
- Create `tailwind.config.js`
- Create `static/input.css`
- **Files**: New files in project root

**Task 1.3**: Update .gitignore
- Add `bin/tailwindcss-*` to ignore binaries
- Add `temp_uploads/css_cache/` for CSS cache
- **Files**: `.gitignore` (+2 lines)

---

### Phase 2: CSS Generation Implementation (1.5-2 hours)

**Task 2.1**: Add CLI path detection
- Implement `_get_tailwind_cli_path()` method
- Detect macOS, Linux, Windows platforms
- **Files**: `pdf_generator.py` (+20 lines)

**Task 2.2**: Implement CSS generation with caching
- Add `generate_tailwind_css()` method
- Create temp HTML file for CLI scanning
- Execute Tailwind CLI via subprocess
- Cache results using MD5 hash
- **Files**: `pdf_generator.py` (+80 lines)

**Task 2.3**: Add cache directory management
- Update `__init__()` to create cache directory
- Add cache cleanup method (optional)
- **Files**: `pdf_generator.py` (+10 lines)

**Task 2.4**: Error handling and fallback
- Try/catch for CLI execution failures
- Fallback to CDN if CSS generation fails
- **Files**: `pdf_generator.py` (+30 lines)

---

### Phase 3: Standalone HTML Generation (1 hour)

**Task 3.1**: Implement standalone HTML builder
- Add `generate_standalone_html()` method
- Combine HTML body + embedded CSS
- Add print-optimized styles
- **Files**: `pdf_generator.py` (+100 lines)

**Task 3.2**: Implement CDN fallback
- Add `_generate_cdn_fallback_html()` method
- Generate HTML with CDN link if CSS fails
- **Files**: `pdf_generator.py` (+40 lines)

**Task 3.3**: Template variable support (if headers/footers exist)
- Apply header/footer content to standalone HTML
- **Files**: `pdf_generator.py` (+20 lines, conditional on FEAT-002)

---

### Phase 4: API Routes (30 min)

**Task 4.1**: Add export HTML endpoint
- `GET /export/{file_id}/html` route
- Load markdown, generate HTML, return as download
- **Files**: `main.py` (+30 lines)

**Task 4.2**: Update preview route (optional optimization)
- Pre-generate CSS for preview if enabled
- **Files**: `main.py` (+10 lines, optional)

---

### Phase 5: Frontend UI (30 min)

**Task 5.1**: Add export button to preview page
- "Download Standalone HTML" button
- Export JavaScript function
- **Files**: `templates/preview.html` (+20 lines)

**Task 5.2**: Add status indicator (optional)
- Show "Generating..." message during export
- **Files**: `templates/preview.html` (+15 lines, optional)

---

### Phase 6: Testing & Optimization (1 hour)

**Task 6.1**: Manual testing
- [ ] Download Tailwind CLI binaries
- [ ] Generate standalone HTML
- [ ] Verify HTML works offline (disable network)
- [ ] Check file size (<30KB typical)
- [ ] Test with various markdown content
- [ ] Test caching (second export should be <1ms)

**Task 6.2**: Performance testing
- [ ] Measure CSS generation time (first run: ~100-200ms, cached: <1ms)
- [ ] Check cache hit rate
- [ ] Monitor cache directory size

**Task 6.3**: Cross-platform testing
- [ ] macOS ARM64
- [ ] macOS x86_64
- [ ] Linux x64
- [ ] Windows (if applicable)

**Task 6.4**: Edge cases
- [ ] Very large markdown (>100KB)
- [ ] Many custom classes (>50)
- [ ] Tailwind CLI not installed (fallback to CDN)
- [ ] Cache directory full (cleanup strategy)

---

## Testing Strategy

### File Size Benchmarks

| Content Type | HTML Body | CDN Version | Standalone Version | Reduction |
|--------------|-----------|-------------|--------------------|-----------|
| Small doc (5KB MD) | 10KB | 310KB | 18KB | 94% |
| Medium doc (20KB MD) | 30KB | 330KB | 25KB | 92% |
| Large doc (100KB MD) | 120KB | 420KB | 135KB | 68% |
| Complex styles (50+ classes) | 15KB | 315KB | 28KB | 91% |

**Target**: 85%+ reduction in file size for typical documents

---

### Performance Benchmarks

| Operation | Target | Acceptable | Unacceptable |
|-----------|--------|------------|--------------|
| CSS generation (first run) | <100ms | <200ms | >500ms |
| CSS generation (cached) | <1ms | <5ms | >10ms |
| Full HTML export | <300ms | <500ms | >1s |
| Cache lookup | <1ms | <5ms | >10ms |

---

### Offline Testing Procedure

1. Generate standalone HTML and download
2. Disconnect from internet (disable WiFi/ethernet)
3. Open downloaded HTML in browser
4. Verify:
   - [ ] All styling appears correctly
   - [ ] Typography (prose classes) works
   - [ ] Code syntax highlighting works
   - [ ] No console errors about missing resources
   - [ ] No broken images (inline content only)

---

### Cross-Browser Testing

| Browser | Embedded CSS | Syntax Highlighting | Print | Status |
|---------|-------------|---------------------|-------|--------|
| Chrome 100+ | ✅ | ✅ | ✅ | Fully Supported |
| Safari 15+ | ✅ | ✅ | ✅ | Fully Supported |
| Firefox 100+ | ✅ | ✅ | ✅ | Fully Supported |
| Edge 100+ | ✅ | ✅ | ✅ | Fully Supported |

---

### Visual Regression Testing

**Procedure**:
1. Generate preview with CDN CSS
2. Generate standalone HTML with embedded CSS
3. Compare visual appearance (screenshot diff)
4. Verify <1% pixel difference

**Tools**: Manual visual comparison (automated diffing optional)

---

## Risk Assessment & Mitigation

### Risk 1: Tailwind CLI Binary Not Installed
**Risk**: User hasn't run `make install-tailwind`
**Likelihood**: Medium (first-time users)
**Impact**: High (HTML export fails)
**Mitigation**:
- Fallback to CDN-based HTML if binary missing
- Show clear error message with installation instructions
- Add check to startup script (warn if binary missing)
- Document binary installation in README

```python
# In generate_tailwind_css()
if not Path(self.tailwind_cli_path).exists():
    print(f"Warning: Tailwind CLI not found. Run 'make install-tailwind'")
    return None  # Trigger CDN fallback
```

---

### Risk 2: CSS Generation Timeout
**Risk**: Very large HTML (>1MB) causes CLI timeout
**Likelihood**: Low (most docs <100KB)
**Impact**: Medium (export fails, no standalone HTML)
**Mitigation**:
- Set 10 second timeout on subprocess
- Fallback to CDN HTML on timeout
- Log timeout events for monitoring

---

### Risk 3: Platform Detection Failure
**Risk**: Unknown platform or architecture
**Likelihood**: Low (covers macOS, Linux, Windows)
**Impact**: High (CLI path wrong, export fails)
**Mitigation**:
- Provide manual CLI path override in config
- Add `TAILWIND_CLI_PATH` environment variable support
- Fallback to CDN if platform detection fails

---

### Risk 4: Cache Directory Growth
**Risk**: CSS cache grows unbounded over time
**Likelihood**: Medium (generates new cache per unique HTML)
**Impact**: Low (disk space usage)
**Mitigation**:
- Implement LRU cache eviction (keep 100 most recent)
- Add cache size limit (e.g., 50MB max)
- Add `make clean-css-cache` command
- Document cache location for manual cleanup

```python
def _cleanup_old_cache(self, max_files=100):
    """Remove oldest cache files if count exceeds max"""
    cache_files = sorted(
        self.css_cache_dir.glob("*.css"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    for old_file in cache_files[max_files:]:
        old_file.unlink()
```

---

### Risk 5: Typography Plugin Missing
**Risk**: Tailwind CLI doesn't include typography plugin
**Likelihood**: Very Low (plugin built into CLI since v3.4)
**Impact**: High (prose classes don't work)
**Mitigation**:
- Verify CLI version supports typography (v3.4+)
- Add version check in installation script
- Document minimum required version

---

## Dependencies & Prerequisites

### Required
- Python 3.8+ (already required)
- Subprocess module (stdlib)
- Hashlib module (stdlib)

### Optional
- None

### System Requirements
- 50MB disk space for Tailwind CLI binaries
- 10-50MB for CSS cache (self-managing with cleanup)
- Write access to `bin/` and `temp_uploads/css_cache/` directories

### External Dependencies
- TailwindCSS Standalone CLI v3.4+ (downloaded via Makefile)
- Internet connection for initial binary download
- No runtime internet dependency (works fully offline after setup)

---

## Future Enhancements (Post-MVP)

### V2 Features
1. **Inline Images**: Convert image URLs to base64 (truly self-contained)
2. **CSS Minification**: Additional gzip compression for smaller files
3. **Multiple Formats**: Export as EPUB, DOCX, PDF (via server-side generation)
4. **Progressive Loading**: Stream HTML generation for large docs
5. **Custom CSS Injection**: Allow users to add custom CSS to embedded styles
6. **Batch Export**: Export multiple markdown files as HTML archive (ZIP)

### Optimization Ideas
- **Pre-warming Cache**: Generate CSS for common prose/class combinations on startup
- **Shared CSS Cache**: Cache CSS based on config only (not HTML content)
- **CDN Mirror**: Self-host Tailwind CSS as fallback (no external CDN)

---

## Success Metrics (Post-Launch)

**Adoption Metrics**:
- % of users who export standalone HTML (target: 30%)
- HTML export vs PDF export ratio (target: 1:3)
- Repeat usage rate (target: 50% export HTML more than once)

**Performance Metrics**:
- Average CSS generation time (target: <100ms first run)
- Cache hit rate (target: >80%)
- File size reduction vs CDN (target: >85%)

**Quality Metrics**:
- Export failure rate (target: <2%)
- Offline functionality rate (target: >95%)
- Visual regression reports (target: <1% pixel diff)

---

## Appendix A: TailwindCSS Purging Research Summary

### Options Evaluated

1. **TailwindCSS CDN JIT Mode** (Current State)
   - Pros: Already implemented, zero setup
   - Cons: 300KB payload, requires internet
   - **Result**: Not suitable for standalone HTML

2. **TailwindCSS Standalone CLI** (Recommended)
   - Pros: Official tool, no Node.js, 5-20KB output, supports typography
   - Cons: Requires binary download, ~100-200ms generation time
   - **Result**: ✅ Selected for implementation

3. **PostCSS + PurgeCSS**
   - Pros: Fine-grained control, 5-15KB output
   - Cons: Requires Node.js, complex setup
   - **Result**: ❌ Rejected (too complex for Python project)

4. **Pre-generated CSS Templates**
   - Pros: Simple, fast (no runtime generation)
   - Cons: Less flexible, larger files (8-15KB vs 5-10KB)
   - **Result**: ⚠️ Alternative approach (easier but less optimal)

---

### File Size Comparisons

| Method | Initial Load | Generated CSS | Offline | Standalone |
|--------|-------------|---------------|---------|------------|
| **Current CDN (JIT)** | ~300KB JS | Minimal | ❌ No | ❌ No |
| **Standalone CLI** | None | 5-20KB | ✅ Yes | ✅ Yes |
| **PostCSS + PurgeCSS** | None | 5-15KB | ✅ Yes | ✅ Yes |
| **Pre-generated** | None | 8-15KB | ✅ Yes | ✅ Yes |

---

### Performance Comparison

| Method | Setup Time | First Generation | Cached Generation |
|--------|-----------|------------------|-------------------|
| CDN | 0 min | N/A | N/A |
| Standalone CLI | 2 min | 100-200ms | <1ms |
| PostCSS | 15 min | 200-500ms | <1ms |
| Pre-generated | 10 min | N/A | <1ms |

---

## Appendix B: Alternative Implementation (Pre-Generated Templates)

If Standalone CLI approach proves problematic, use pre-generated CSS:

**Setup**:
```bash
# One-time: Generate CSS for common configurations
./bin/tailwindcss -i static/input.css -o static/css/prose-sm.min.css --content="templates/sample-sm.html" --minify
./bin/tailwindcss -i static/input.css -o static/css/prose.min.css --content="templates/sample.html" --minify
./bin/tailwindcss -i static/input.css -o static/css/prose-lg.min.css --content="templates/sample-lg.html" --minify
```

**Usage**:
```python
def get_css_for_config(config: dict) -> str:
    """Get pre-generated CSS for configuration"""
    prose_size = config.get('prose_size', 'prose').replace('prose-', '')
    css_file = Path(f'static/css/prose-{prose_size}.min.css')

    if not css_file.exists():
        css_file = Path('static/css/prose.min.css')  # Fallback

    return css_file.read_text()
```

**Pros**:
- Simpler (no subprocess calls)
- Faster (no runtime generation)
- No cache management

**Cons**:
- Less flexible (doesn't adapt to custom classes well)
- Larger files (~10-15KB vs 5-8KB with purging)
- Must regenerate when adding new classes

---

## File Locations Summary

```
New Files:
  bin/tailwindcss-macos       → Downloaded via Makefile
  bin/tailwindcss-linux       → Downloaded via Makefile
  tailwind.config.js          → New config file
  static/input.css            → New TailwindCSS source

Modified Files:
  pdf_generator.py            → +250 lines (CSS generation, standalone HTML)
  main.py                     → +35 lines (export route)
  templates/preview.html      → +25 lines (export button)
  Makefile                    → +10 lines (install-tailwind target)
  .gitignore                  → +2 lines (bin/, css_cache/)

Generated Files:
  temp_uploads/css_cache/     → CSS cache directory
    {hash}.css                → Cached purged CSS files
```

---

**Total Estimated Effort**: 4-5 hours
**Priority**: Medium-High
**Status**: Ready for implementation

---

## Installation Instructions (User-Facing)

Add to project README:

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
