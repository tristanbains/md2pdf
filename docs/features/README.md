# MD2PDF Feature PRDs

This directory contains detailed Product Requirements Documents (PRDs) for planned MD2PDF features.

---

## Feature Overview

| Feature | Priority | Complexity | Effort | Risk | Status |
|---------|----------|-----------|--------|------|--------|
| [Settings Presets](#feat-001-settings-presets) | High | Medium | 3-4 hours | Low | Planned |
| [Page Headers/Footers](#feat-002-page-headers--footers) | High | High | 5-6 hours | Medium | Planned |
| [Standalone HTML Export](#feat-003-standalone-html-export) | Medium-High | Medium-High | 4-5 hours | Medium | Planned |

**Total Estimated Effort**: 12-15 hours

---

## FEAT-001: Settings Presets

**File**: [`prd-settings-presets.md`](./prd-settings-presets.md)

### Summary
Save and load named configuration presets. Users can create custom presets, switch between them instantly, and share preset files with colleagues via export/import.

### Key Capabilities
- Save current settings as named preset (e.g., "Academic", "Blog", "Dark Mode")
- Load preset to apply all configuration at once
- Export/import presets as YAML files for sharing
- Factory presets included (Default, Minimal, Academic, Dark Mode)
- Preset management UI (dropdown, save modal, delete confirmation)

### Technical Approach
- YAML file storage in `~/Library/Application Support/md2pdf/presets/`
- Factory presets (read-only) + user presets (editable)
- Metadata tracking (name, description, author, created date)
- Import validation and security (filename sanitization)

### Effort Breakdown
- **Phase 1**: Backend foundation (1-1.5 hours)
  - Preset CRUD methods, directory structure, validation
- **Phase 2**: API routes (1 hour)
  - Save, load, delete, export, import endpoints
- **Phase 3**: Frontend UI (1-1.5 hours)
  - Preset selector, save modal, import/export handlers
- **Phase 4**: Testing & polish (0.5-1 hour)

### Dependencies
- None (uses existing YAML config infrastructure)

### Risks
- Low risk - straightforward file operations
- Main consideration: filename validation to prevent path traversal

---

## FEAT-002: Page Headers & Footers

**File**: [`prd-page-headers-footers.md`](./prd-page-headers-footers.md)

### Summary
Add customizable headers and footers to every page of generated PDFs. Supports dynamic content via template variables (`{page}`, `{total_pages}`, `{filename}`, `{date}`).

### Key Capabilities
- Enable/disable headers and footers independently
- Template variables: `{page}`, `{total_pages}`, `{filename}`, `{date}`, `{time}`, `{datetime}`
- Styling controls: alignment, font size, color, borders
- Automatic page numbering option (append "Page X of Y" to footer)
- Professional formatting (borders, backgrounds, padding)

### Technical Approach
- **HTML structure injection** (not CSS `@page` rules)
  - More reliable across browsers
  - Better support for dynamic content
- Fixed positioning with print media queries
- JavaScript for page counter approximation
- Server-side template variable replacement

### Effort Breakdown
- **Phase 1**: Backend configuration (1.5 hours)
  - Config schema, template variable replacement
- **Phase 2**: API routes (1 hour)
  - Update config endpoint with 13 new form fields
- **Phase 3**: Frontend UI (2-2.5 hours)
  - Header/footer sections in settings form, toggle visibility
- **Phase 4**: Template rendering (1-1.5 hours)
  - Update preview.html with header/footer divs, CSS
- **Phase 5**: Testing & polish (1 hour)
  - Multi-page testing, browser compatibility

### Dependencies
- None (uses existing template infrastructure)

### Risks
- **Medium risk** - Browser-based page numbering is approximate
- Content overlap possible on page breaks (needs careful margin management)
- **Security**: Must escape user input to prevent XSS (use `| e` not `| safe`)

### Limitations
- Page counters `{page}` and `{total_pages}` are approximate in browser print
- True page numbering requires server-side PDF generation (future enhancement)
- Document limitation clearly in UI

---

## FEAT-003: Standalone HTML Export

**File**: [`prd-standalone-html-export.md`](./prd-standalone-html-export.md)

### Summary
Export markdown as standalone HTML files with embedded CSS. Files work offline without CDN dependencies, achieving 85%+ file size reduction (20-30KB vs 300KB+ with CDN).

### Key Capabilities
- Generate self-contained HTML with embedded TailwindCSS
- Works offline (no internet required after download)
- Optimized file size (5-20KB CSS vs 300KB CDN)
- Maintains identical appearance to preview
- Downloadable from preview page
- Fallback to CDN if CSS generation fails

### Technical Approach
- **TailwindCSS Standalone CLI** with caching
  - No Node.js required (Python-first approach)
  - Official tool from Tailwind Labs
  - Subprocess call to CLI binary for CSS purging
  - MD5-based caching for performance (<1ms cached lookups)
- Cross-platform binaries (macOS, Linux, Windows)
- Embedded CodeHilite CSS for syntax highlighting

### Effort Breakdown
- **Phase 1**: Setup & binary management (30 min)
  - Makefile target to download CLI, config files
- **Phase 2**: CSS generation implementation (1.5-2 hours)
  - CLI path detection, subprocess execution, caching
- **Phase 3**: Standalone HTML generation (1 hour)
  - Build complete HTML document with embedded CSS
- **Phase 4**: API routes (30 min)
  - Export endpoint with file download
- **Phase 5**: Frontend UI (30 min)
  - Export button on preview page
- **Phase 6**: Testing & optimization (1 hour)
  - Offline testing, file size verification, caching validation

### Dependencies
- **External**: TailwindCSS Standalone CLI v3.4+ (downloaded via Makefile)
- **Python**: subprocess, hashlib (stdlib)
- **System**: 50MB disk space for binaries, 10-50MB for cache

### Risks
- **Medium risk** - Requires binary download (fallback to CDN if missing)
- CSS generation timeout for very large HTML (mitigated with 10s timeout)
- Cache directory growth (mitigated with LRU eviction, max 100 files)
- Platform detection failure (mitigated with manual path override option)

### Research Findings
Evaluated 4 approaches:
1. ❌ **CDN JIT Mode** - Requires internet (doesn't solve offline use case)
2. ✅ **Standalone CLI** - Selected (no Node.js, official, 5-20KB output)
3. ❌ **PostCSS + PurgeCSS** - Rejected (requires Node.js ecosystem)
4. ⚠️ **Pre-generated Templates** - Alternative (simpler but less flexible)

---

## Implementation Recommendations

### Suggested Order

**Phase 1: Settings Presets** (Week 1)
- Lowest risk, foundational feature
- Enables saving header/footer configs later
- Quick win for user productivity

**Phase 2: Standalone HTML Export** (Week 2)
- Independent of other features
- High user value (offline access, sharing)
- Validates TailwindCSS approach

**Phase 3: Page Headers/Footers** (Week 3)
- Most complex, highest risk
- Benefits from preset system (save header configs)
- Completes professional document formatting

### Dependencies Between Features

```
Settings Presets (FEAT-001)
  ↓ (optional: save header/footer configs)
Page Headers/Footers (FEAT-002)

Standalone HTML Export (FEAT-003)
  ↓ (can embed headers/footers if FEAT-002 implemented)
Page Headers/Footers (FEAT-002)
```

**Note**: Features can be implemented independently, but presets enable saving header/footer configurations.

---

## Testing Strategy

### Per-Feature Testing
Each PRD includes:
- Manual testing checklist
- Browser compatibility matrix
- Edge case scenarios
- Performance benchmarks

### Integration Testing (After All Features)
1. **Create preset with headers/footers** → Export as standalone HTML
   - Verify headers/footers appear in exported HTML
   - Confirm offline functionality

2. **Test preset export/import** → Load preset → Generate standalone HTML
   - Verify imported presets work correctly
   - Confirm CSS generation uses preset config

3. **Cross-browser validation**
   - All features work in Chrome, Safari, Firefox, Edge

---

## Success Metrics

### Feature Adoption
- **Presets**: 60% of users create at least 1 custom preset
- **Headers/Footers**: 50% of users enable footers (40% enable headers)
- **Standalone HTML**: 30% of users export HTML at least once

### Performance
- **Presets**: Preset load <100ms
- **Headers/Footers**: No pagination issues reported
- **Standalone HTML**: CSS generation <200ms (first run), <1ms (cached)

### Quality
- **All Features**: <2% error rate, <5 user-reported issues per feature

---

## Documentation Updates Required

After implementation, update:

1. **CLAUDE.md**
   - Add presets overview and usage
   - Document header/footer template variables
   - Explain standalone HTML export and TailwindCSS CLI

2. **docs/implementation-details.md**
   - Preset file format specification
   - Header/footer template variable reference
   - CSS generation pipeline details

3. **docs/development-patterns.md**
   - Adding new preset fields pattern
   - Template variable expansion pattern
   - CSS caching strategy

4. **README.md**
   - Installation instructions for TailwindCSS CLI
   - Feature highlights with screenshots
   - Export options (PDF vs HTML)

---

## Future Enhancements (Post-MVP)

### V2 Feature Ideas

**Presets V2**:
- Preset preview (show sample before applying)
- Preset tags and categories
- Cloud sync across devices

**Headers/Footers V2**:
- Image support (logos)
- First page different headers
- Odd/even page variations
- Server-side PDF generation for accurate page numbers

**Standalone HTML V2**:
- Inline images as base64
- Multiple export formats (EPUB, DOCX)
- Batch export (ZIP archive of multiple files)
- Progressive loading for large documents

---

## Contact & Feedback

These PRDs are living documents. For questions, clarifications, or suggestions:
- Open an issue on GitHub
- Update PRDs directly based on implementation learnings
- Add "Implementation Notes" sections to PRDs during development

---

**Last Updated**: 2025-01-30
**Status**: All PRDs ready for implementation
