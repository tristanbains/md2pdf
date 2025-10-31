# PRD: Settings Preset Management System (Summary)

**Feature ID**: `FEAT-001`
**Status**: Planned
**Priority**: High
**Complexity**: Medium (3-4 hours)
**Risk Level**: Low

**Full Specification**: See `prd-settings-presets-full.md` for complete implementation details

---

## Executive Summary

Add a preset management system that allows users to save, load, export, import, and share their custom styling configurations. Users can create named presets (e.g., "Academic Paper", "Dark Mode", "Minimal"), switch between them instantly, and share preset files with colleagues. The system includes factory presets for common use cases and supports import/export for sharing across installations.

---

## Problem Statement

### Current Limitations
- Users must manually configure 25+ styling options for each use case
- Settings are global - no way to have different configurations for different document types
- No way to revert to a specific configuration without manual backup
- Factory reset is the only preset available
- Cannot share configurations with team members or across machines

### User Pain Points
1. **Repetitive Configuration**: Academic users need formal styling, blog users need casual styling - must reconfigure each time
2. **No Experimentation Safety**: Users fear breaking working configurations when trying new styles
3. **Team Collaboration**: Design teams can't standardize on shared styling across members
4. **Context Switching**: Users working on multiple project types must remember/recreate settings

---

## Goals & Success Metrics

### Primary Goals
1. Enable instant switching between multiple saved configurations
2. Provide curated factory presets for common use cases
3. Allow users to export/import presets for sharing and backup
4. Maintain backwards compatibility with existing config.yaml

### Success Metrics
- Users create average of 3+ custom presets within first week
- 70%+ of users utilize at least one factory preset
- Zero data loss incidents during preset operations
- Import/export feature used for team collaboration

### Non-Goals (Out of Scope)
- Cloud-based preset syncing
- Preset marketplace or community sharing platform
- Version control for presets
- Preset preview before applying

---

## User Stories (Condensed)

### Story 1: Academic Researcher
Save "formal paper" styling as preset, apply instantly to all research papers, export to share with co-authors.

### Story 2: Content Creator
Switch between "blog post" and "documentation" presets without manual reconfiguration, with unsaved changes warning.

### Story 3: Design Team Lead
Export company style guide as preset file for team members to import and use consistently.

### Story 4: New User
Try factory presets for common use cases before creating custom configurations.

---

## Technical Architecture (High-Level)

### Storage Structure
```
~/Library/Application Support/md2pdf/
├── config.yaml                    # Current active configuration
└── presets/
    ├── factory/                   # Built-in presets (read-only)
    │   ├── default.yaml
    │   ├── minimal.yaml
    │   ├── academic.yaml
    │   └── dark-mode.yaml
    └── user/                      # User-created presets
        ├── my-blog.yaml
        └── work-docs.yaml
```

### Preset File Format
- **Format**: YAML with optional metadata section + full config
- **Metadata**: name, description, author, created_at, version, is_factory
- **Content**: All config fields (prose_size, prose_color, codehilite_theme, custom_classes, etc.)
- **Naming**: Slugified (lowercase, spaces→dashes, 50 char max)

### Security & Validation
- Uses `yaml.safe_load()` to prevent code injection
- Path traversal protection (blocks `../`, `/`, `\`)
- Schema validation for required fields
- Allowed characters: `a-z A-Z 0-9 - _ (space)`
- Forbidden names: `config`, `temp`, `default`

---

## API Endpoints

### 1. List All Presets
- **Route**: `GET /api/presets`
- **Returns**: JSON with factory and user preset lists

### 2. Save Current Config as Preset
- **Route**: `POST /api/presets/save`
- **Params**: `name` (required), `description` (optional)
- **Action**: Saves current config to user presets directory

### 3. Load Preset
- **Route**: `POST /api/presets/load/{slug}`
- **Action**: Applies preset to config, updates all form fields, saves to config.yaml

### 4. Delete Preset
- **Route**: `DELETE /api/presets/delete/{slug}`
- **Action**: Removes user preset (cannot delete factory presets)

### 5. Export Preset
- **Route**: `GET /api/presets/export/{slug}`
- **Returns**: Downloadable YAML file (`{name}.md2pdf-preset.yaml`)

### 6. Import Preset
- **Route**: `POST /api/presets/import`
- **Params**: `file` (YAML upload), `name` (optional rename)
- **Action**: Validates and saves to user presets

---

## PDFGenerator Changes

### New Methods
- `_ensure_presets_directory()` - Create directory structure on init
- `_create_factory_presets()` - Generate built-in presets on first run
- `list_presets()` - Return factory + user preset metadata
- `save_preset(name, description)` - Save current config as preset
- `load_preset(slug)` - Load and apply preset configuration
- `delete_preset(slug)` - Remove user preset file
- `export_preset(slug)` - Return preset file path for download
- `import_preset(file_content, name)` - Parse and save uploaded preset
- `_validate_preset_config(config)` - Validate required fields
- `_load_preset_metadata(path)` - Extract metadata without full load

### Factory Preset Configurations
- **Default**: Original MD2PDF defaults
- **Minimal**: Small prose size, no custom classes
- **Academic**: Large prose, formal styling, border on h1, blue blockquotes
- **Dark Mode**: Inverted prose, dark background, light text, monokai theme

---

## UI/UX Components

### Presets Section (Settings Form)
**Location**: Top of settings form, before "Prose Size"

**Components**:
- Dropdown selector with factory/user preset groups
- "Load" button (with unsaved changes warning)
- "Save as Preset..." button (opens modal)
- "Export..." button (downloads selected preset)
- "Import..." button (file picker)
- "Delete" button (disabled for factory presets, confirmation dialog)
- Status message area

### Save Preset Modal
**Fields**:
- Preset name input (50 char max, validation feedback)
- Description textarea (optional)
- Cancel/Save buttons

### JavaScript Functions
- `loadPresets()` - Fetch and populate dropdown on page load
- `updatePresetDropdown()` - Render factory/user preset options
- Load handler with unsaved changes warning
- Save modal handlers (validation, API call, close)
- Export handler (trigger download)
- Import handler (file picker, upload, validation)
- Delete handler (confirmation, API call, refresh)
- `applyConfigToForm(config)` - Update all 25 form fields from loaded preset
- `showStatus(message, type)` - Display success/error messages

---

## Implementation Roadmap

### Phase 1: Backend Foundation (1-1.5 hours)
1. Create preset directory structure in `PDFGenerator.__init__()`
2. Add `validate_preset_name()` helper function
3. Implement CRUD methods (save, load, delete, list)
4. Create factory preset generators (minimal, academic, dark-mode)

**Files**: `pdf_generator.py` (~250 lines added)

### Phase 2: API Routes (1 hour)
1. List presets endpoint
2. Save preset endpoint
3. Load preset endpoint
4. Delete preset endpoint
5. Export preset endpoint (FileResponse)
6. Import preset endpoint (UploadFile)

**Files**: `main.py` (~150 lines added)

### Phase 3: Frontend UI (1-1.5 hours)
1. Add presets section HTML to settings form
2. Create save preset modal
3. Implement JavaScript handlers for all actions
4. Add preset dropdown population logic
5. Implement unsaved changes warning
6. Add success/error status display

**Files**: `templates/index.html` (~200 lines added)

### Phase 4: Testing & Polish (0.5-1 hour)
1. Manual testing (create, load, export, import, delete)
2. Edge case testing (long names, special characters, malformed YAML, conflicts)
3. Update documentation (`CLAUDE.md`, `docs/implementation-details.md`)

---

## Sharing Workflow

### Export Process (User A)
1. Configure styling or select existing preset
2. Click "Save as Preset..." → name it (e.g., "Company Style")
3. Select preset from dropdown
4. Click "Export..." → downloads `company-style.md2pdf-preset.yaml`
5. Share file via email/Slack/shared drive

### Import Process (User B)
1. Receive `.md2pdf-preset.yaml` file
2. Click "Import..." button, select file
3. System validates YAML structure and required fields
4. Preset appears in "My Presets" dropdown
5. Click "Load" to apply styling

### Conflict Handling
- If preset name exists: Show overwrite confirmation
- No automatic versioning (no "Preset (1)", "Preset (2)")
- Best practice: Include version/date in preset names

---

## Risk Assessment & Mitigation

### Risk 1: File System Permissions
**Mitigation**: Error handling with fallback to project directory

### Risk 2: Preset Name Collisions
**Mitigation**: Check for existing preset, show confirmation dialog before overwrite

### Risk 3: Malicious Preset Import
**Mitigation**: Use `yaml.safe_load()`, validate schema, sanitize names

### Risk 4: Backwards Compatibility
**Mitigation**: Preset system is additive only, doesn't modify existing config structure

---

## Testing Checklist (Quick Reference)

**Core Functions**:
- [ ] Save current settings as preset
- [ ] Load preset updates all form fields
- [ ] Export preset downloads YAML file
- [ ] Import preset validates and adds to dropdown
- [ ] Delete preset removes from list (factory presets disabled)

**Edge Cases**:
- [ ] 50 character preset name (max length)
- [ ] Special characters in name (should fail)
- [ ] Malformed YAML import (should error)
- [ ] Preset name collision (should prompt)
- [ ] Unsaved changes warning when loading preset

---

## Dependencies & Prerequisites

### Required
- Python 3.8+ ✓ (already required)
- PyYAML ✓ (already installed)
- FastAPI ✓ (already installed)

### System Requirements
- Write access to `~/Library/Application Support/md2pdf/`
- ~1MB disk space for presets directory

---

## Future Enhancements (Post-MVP)

**V2 Features**:
- Preset preview before loading
- Preset versioning and history
- Preset tags and search
- Batch export (all presets as ZIP)
- Cloud sync across devices

**Integration Ideas**:
- CLI support: `md2pdf --preset academic input.md output.pdf`
- Preset marketplace for community sharing
- AI preset generator from natural language

---

## Success Metrics (Post-Launch)

**Adoption**:
- 60%+ of users create at least 1 custom preset
- Average 3-5 presets per active user
- Track which factory presets are most popular

**Engagement**:
- 2-3 preset loads per session
- Export/import usage indicates team collaboration
- Time saved: ~30-60 seconds per preset switch vs manual config

**Quality**:
- <1% preset-related error rate
- <5 user-reported issues with preset system

---

## Quick File Reference

```
Modified Files:
  pdf_generator.py          +250 lines
  main.py                   +150 lines
  templates/index.html      +200 lines

Generated Files:
  ~/Library/Application Support/md2pdf/presets/factory/*.yaml (4 files)
  ~/Library/Application Support/md2pdf/presets/user/*.yaml (user-created)
```

---

**Total Estimated Effort**: 3-4 hours
**Implementation Difficulty**: Medium
**User Impact**: High (eliminates repetitive configuration)

For complete API specifications, code examples, and detailed implementation guidance, see **`prd-settings-presets-full.md`**.
