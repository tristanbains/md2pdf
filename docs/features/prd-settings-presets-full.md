# PRD: Settings Preset Management System

**Feature ID**: `FEAT-001`
**Status**: Planned
**Priority**: High
**Complexity**: Medium (3-4 hours)
**Risk Level**: Low

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
- Import/export feature used for team collaboration (measured by survey)

### Non-Goals (Out of Scope)
- Cloud-based preset syncing
- Preset marketplace or community sharing platform
- Version control for presets
- Preset preview before applying

---

## User Stories & Use Cases

### User Story 1: Academic Researcher
**As an** academic researcher
**I want to** save my "formal paper" styling as a preset
**So that** I can instantly apply professional formatting to all my research papers

**Acceptance Criteria**:
- Can save current config as "Academic" preset with one click
- Preset appears in dropdown list immediately
- Loading preset applies all 25 configuration fields
- Can export preset to share with co-authors

### User Story 2: Content Creator
**As a** technical blogger
**I want to** switch between "blog post" and "documentation" presets
**So that** I can match styling to different content types without manual reconfiguration

**Acceptance Criteria**:
- Can create multiple named presets (Blog, Docs, GitHub)
- Dropdown shows all presets with current one highlighted
- Switching presets updates all form fields in UI
- Unsaved changes warning appears if switching with modifications

### User Story 3: Design Team Lead
**As a** design team lead
**I want to** export our company style guide as a preset file
**So that** all team members can import and use consistent PDF styling

**Acceptance Criteria**:
- Export generates downloadable .yaml file
- Import accepts .yaml files via file picker
- Imported presets validate against schema
- Malformed imports show clear error messages

### User Story 4: New User
**As a** first-time user
**I want to** try factory presets for common use cases
**So that** I can see what's possible before creating custom configurations

**Acceptance Criteria**:
- App ships with 4+ factory presets
- Factory presets cannot be deleted (only hidden)
- Each factory preset has clear description
- Factory reset returns to "Factory Default" preset

---

## Technical Specifications

### Architecture Overview

```
~/Library/Application Support/md2pdf/
├── config.yaml                    # Current active configuration
├── presets/                       # Preset storage directory
│   ├── factory/                  # Built-in presets (read-only)
│   │   ├── default.yaml
│   │   ├── minimal.yaml
│   │   ├── academic.yaml
│   │   └── dark-mode.yaml
│   └── user/                     # User-created presets
│       ├── my-blog.yaml
│       ├── work-docs.yaml
│       └── ...
```

### Data Model

#### Preset File Structure (YAML)
```yaml
# metadata (optional, for UI display)
_metadata:
  name: "Academic Paper"
  description: "Professional formatting for research papers"
  author: "user@example.com"
  created_at: "2025-01-15T10:30:00Z"
  version: "1.0"

# configuration (same structure as config.yaml)
prose_size: "prose-lg"
prose_color: "prose-slate"
codehilite_theme: "github-dark"
codehilite_container:
  auto_background: true
  custom_background: ""
  wrapper_classes: "p-4 rounded-lg overflow-x-auto my-4"
custom_classes:
  h1: "text-4xl font-bold text-gray-900"
  h2: "text-3xl font-semibold text-gray-800"
  # ... all 22 element classes
```

#### Preset Metadata
```python
@dataclass
class PresetMetadata:
    name: str                    # Display name
    description: str = ""        # Optional description
    author: str = ""            # Creator email/name
    created_at: datetime = None  # Creation timestamp
    version: str = "1.0"        # Preset format version
    is_factory: bool = False    # True for built-in presets
```

### File Naming & Validation

**Allowed Characters**: `a-z A-Z 0-9 - _ (space)`
**Max Length**: 50 characters
**Forbidden Names**: `config`, `temp`, `.`, `..`

**Validation Function**:
```python
import re

def validate_preset_name(name: str) -> tuple[bool, str]:
    """Validate preset name. Returns (is_valid, error_message)"""
    if not name or len(name) == 0:
        return False, "Preset name cannot be empty"

    if len(name) > 50:
        return False, "Preset name too long (max 50 characters)"

    # Sanitize: only alphanumeric, dash, underscore, space
    if not re.match(r'^[a-zA-Z0-9\s_-]+$', name):
        return False, "Invalid characters in preset name (use letters, numbers, spaces, dashes, underscores)"

    # Prevent directory traversal
    if '..' in name or '/' in name or '\\' in name:
        return False, "Invalid preset name"

    # Reserved names
    forbidden = ['config', 'temp', 'default']
    if name.lower() in forbidden:
        return False, f"'{name}' is a reserved name"

    return True, ""
```

---

## API Design

### Backend Routes

#### 1. List All Presets
```python
@app.get("/api/presets")
async def list_presets() -> JSONResponse
```

**Response**:
```json
{
  "factory": [
    {
      "name": "Factory Default",
      "slug": "default",
      "description": "Original MD2PDF defaults",
      "is_factory": true,
      "can_delete": false
    },
    {
      "name": "Minimal",
      "slug": "minimal",
      "description": "Clean styling with minimal classes",
      "is_factory": true,
      "can_delete": false
    }
  ],
  "user": [
    {
      "name": "My Blog Style",
      "slug": "my-blog",
      "description": "Personal blog formatting",
      "is_factory": false,
      "can_delete": true,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

#### 2. Save Current Config as Preset
```python
@app.post("/api/presets/save")
async def save_preset(
    name: str = Form(...),
    description: str = Form("")
) -> JSONResponse
```

**Behavior**:
1. Validate preset name
2. Get current configuration from `PDFGenerator.config`
3. Add metadata (name, description, timestamp, author)
4. Save to `~/Library/Application Support/md2pdf/presets/user/{slug}.yaml`
5. If preset exists, prompt for overwrite confirmation (handled in frontend)

**Response**:
```json
{
  "status": "success",
  "message": "Preset 'My Blog Style' saved successfully",
  "preset": {
    "name": "My Blog Style",
    "slug": "my-blog",
    "path": "presets/user/my-blog.yaml"
  }
}
```

**Error Response** (400):
```json
{
  "error": "Invalid preset name (use letters, numbers, spaces, dashes, underscores)"
}
```

---

#### 3. Load Preset
```python
@app.post("/api/presets/load/{slug}")
async def load_preset(slug: str) -> JSONResponse
```

**Behavior**:
1. Check factory presets first: `presets/factory/{slug}.yaml`
2. Check user presets: `presets/user/{slug}.yaml`
3. Load YAML configuration
4. Update `PDFGenerator.config` with preset values
5. Save to main `config.yaml` (makes it the active config)
6. Return full configuration for frontend to update form

**Response**:
```json
{
  "status": "success",
  "message": "Preset 'Academic' loaded successfully",
  "config": {
    "prose_size": "prose-lg",
    "prose_color": "prose-slate",
    "codehilite_theme": "github-dark",
    "custom_classes": { /* ... */ }
  }
}
```

---

#### 4. Delete Preset
```python
@app.delete("/api/presets/delete/{slug}")
async def delete_preset(slug: str) -> JSONResponse
```

**Behavior**:
1. Verify slug exists in user presets (cannot delete factory)
2. Delete file: `presets/user/{slug}.yaml`
3. Return success

**Response**:
```json
{
  "status": "success",
  "message": "Preset 'old-style' deleted successfully"
}
```

**Error Response** (403):
```json
{
  "error": "Cannot delete factory presets"
}
```

---

#### 5. Export Preset
```python
@app.get("/api/presets/export/{slug}")
async def export_preset(slug: str) -> FileResponse
```

**Behavior**:
1. Load preset from factory or user directory
2. Return as downloadable YAML file
3. Set filename: `{name}.md2pdf-preset.yaml`

**Response Headers**:
```
Content-Type: application/x-yaml
Content-Disposition: attachment; filename="academic.md2pdf-preset.yaml"
```

---

#### 6. Import Preset
```python
@app.post("/api/presets/import")
async def import_preset(
    file: UploadFile = File(...),
    name: str = Form(None)  # Optional: rename on import
) -> JSONResponse
```

**Behavior**:
1. Validate file extension (`.yaml` or `.yml`)
2. Parse YAML content
3. Validate against config schema
4. Extract metadata if present
5. Use provided name or metadata name or filename
6. Save to `presets/user/{slug}.yaml`

**Response**:
```json
{
  "status": "success",
  "message": "Preset 'Team Style' imported successfully",
  "preset": {
    "name": "Team Style",
    "slug": "team-style"
  }
}
```

**Error Response** (400):
```json
{
  "error": "Invalid preset file: missing required field 'prose_size'"
}
```

---

## PDFGenerator Class Changes

### New Methods

```python
class PDFGenerator:
    def __init__(self, config_path: str = None):
        # ... existing code ...
        self.presets_dir = self.config_path.parent / "presets"
        self.factory_presets_dir = self.presets_dir / "factory"
        self.user_presets_dir = self.presets_dir / "user"
        self._ensure_presets_directory()

    def _ensure_presets_directory(self):
        """Create presets directory structure if it doesn't exist"""
        self.factory_presets_dir.mkdir(parents=True, exist_ok=True)
        self.user_presets_dir.mkdir(parents=True, exist_ok=True)
        self._create_factory_presets()

    def _create_factory_presets(self):
        """Create built-in factory presets if they don't exist"""
        factory_presets = {
            'default': self.get_default_config(),
            'minimal': self._get_minimal_config(),
            'academic': self._get_academic_config(),
            'dark-mode': self._get_dark_mode_config()
        }

        for name, config in factory_presets.items():
            preset_path = self.factory_presets_dir / f"{name}.yaml"
            if not preset_path.exists():
                with open(preset_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)

    def list_presets(self) -> dict:
        """List all available presets (factory + user)"""
        factory = []
        user = []

        # Factory presets
        for preset_file in self.factory_presets_dir.glob("*.yaml"):
            preset = self._load_preset_metadata(preset_file)
            preset['is_factory'] = True
            preset['can_delete'] = False
            factory.append(preset)

        # User presets
        for preset_file in self.user_presets_dir.glob("*.yaml"):
            preset = self._load_preset_metadata(preset_file)
            preset['is_factory'] = False
            preset['can_delete'] = True
            user.append(preset)

        return {'factory': factory, 'user': user}

    def _load_preset_metadata(self, preset_path: Path) -> dict:
        """Load preset metadata without loading full config"""
        with open(preset_path, 'r') as f:
            data = yaml.safe_load(f)

        metadata = data.get('_metadata', {})
        slug = preset_path.stem

        return {
            'name': metadata.get('name', slug.replace('-', ' ').title()),
            'slug': slug,
            'description': metadata.get('description', ''),
            'created_at': metadata.get('created_at'),
            'author': metadata.get('author', '')
        }

    def save_preset(self, name: str, description: str = "") -> str:
        """Save current config as a named preset"""
        # Validate name
        is_valid, error_msg = validate_preset_name(name)
        if not is_valid:
            raise ValueError(error_msg)

        # Create slug from name
        slug = name.lower().replace(' ', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug)

        # Add metadata
        preset_config = {
            '_metadata': {
                'name': name,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'version': '1.0'
            },
            **self.config
        }

        # Save to user presets
        preset_path = self.user_presets_dir / f"{slug}.yaml"
        with open(preset_path, 'w') as f:
            yaml.dump(preset_config, f, default_flow_style=False)

        return slug

    def load_preset(self, slug: str) -> dict:
        """Load preset by slug and apply to current config"""
        # Check factory first, then user
        preset_path = self.factory_presets_dir / f"{slug}.yaml"
        if not preset_path.exists():
            preset_path = self.user_presets_dir / f"{slug}.yaml"

        if not preset_path.exists():
            raise FileNotFoundError(f"Preset '{slug}' not found")

        # Load preset
        with open(preset_path, 'r') as f:
            preset_data = yaml.safe_load(f)

        # Remove metadata before applying
        preset_data.pop('_metadata', None)

        # Apply to current config and save
        self.config.update(preset_data)
        self.save_config()

        return self.config

    def delete_preset(self, slug: str):
        """Delete user preset (cannot delete factory)"""
        preset_path = self.user_presets_dir / f"{slug}.yaml"

        if not preset_path.exists():
            raise FileNotFoundError(f"Preset '{slug}' not found")

        preset_path.unlink()

    def export_preset(self, slug: str) -> Path:
        """Get path to preset file for export"""
        # Check factory first, then user
        preset_path = self.factory_presets_dir / f"{slug}.yaml"
        if not preset_path.exists():
            preset_path = self.user_presets_dir / f"{slug}.yaml"

        if not preset_path.exists():
            raise FileNotFoundError(f"Preset '{slug}' not found")

        return preset_path

    def import_preset(self, file_content: bytes, name: str = None) -> str:
        """Import preset from uploaded YAML file"""
        # Parse YAML
        try:
            preset_data = yaml.safe_load(file_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML file: {e}")

        # Extract name from metadata or use provided
        if name is None:
            metadata = preset_data.get('_metadata', {})
            name = metadata.get('name', 'Imported Preset')

        # Validate config structure
        self._validate_preset_config(preset_data)

        # Save as new preset
        slug = self.save_preset(name, preset_data.get('_metadata', {}).get('description', ''))

        return slug

    def _validate_preset_config(self, config: dict):
        """Validate preset config has required fields"""
        required_fields = ['prose_size', 'prose_color', 'codehilite_theme',
                          'codehilite_container', 'custom_classes']

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Invalid preset: missing required field '{field}'")

    @staticmethod
    def _get_minimal_config() -> dict:
        """Factory preset: minimal styling"""
        config = PDFGenerator.get_default_config()
        config['prose_size'] = 'prose-sm'
        config['prose_color'] = ''
        config['custom_classes'] = {k: '' for k in config['custom_classes']}
        return config

    @staticmethod
    def _get_academic_config() -> dict:
        """Factory preset: academic/formal styling"""
        config = PDFGenerator.get_default_config()
        config['prose_size'] = 'prose-lg'
        config['prose_color'] = 'prose-slate'
        config['custom_classes']['h1'] = 'text-4xl font-bold text-gray-900 border-b-2 pb-2'
        config['custom_classes']['h2'] = 'text-3xl font-semibold text-gray-800 mt-8'
        config['custom_classes']['blockquote'] = 'border-l-4 border-blue-500 pl-4 italic'
        return config

    @staticmethod
    def _get_dark_mode_config() -> dict:
        """Factory preset: dark theme"""
        config = PDFGenerator.get_default_config()
        config['prose_color'] = 'prose-invert'
        config['codehilite_theme'] = 'monokai'
        config['custom_classes']['body'] = 'bg-gray-900 text-gray-100'
        return config
```

---

## UI/UX Design

### Settings Form Layout Changes

Add new "Presets" section at the top of the settings form (before "Prose Size"):

```html
<!-- NEW: Presets Section -->
<div class="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
    <h3 class="text-lg font-semibold mb-3">Presets</h3>

    <!-- Preset Selector -->
    <div class="flex gap-2 mb-3">
        <select id="preset-selector" class="flex-1 border rounded px-3 py-2">
            <option value="">-- Current Settings --</option>
            <optgroup label="Factory Presets">
                <!-- Populated dynamically -->
            </optgroup>
            <optgroup label="My Presets">
                <!-- Populated dynamically -->
            </optgroup>
        </select>

        <button id="load-preset-btn" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            Load
        </button>
    </div>

    <!-- Preset Actions -->
    <div class="flex gap-2">
        <button id="save-preset-btn" class="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm">
            Save as Preset...
        </button>

        <button id="export-preset-btn" class="px-3 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 text-sm">
            Export...
        </button>

        <button id="import-preset-btn" class="px-3 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 text-sm">
            Import...
        </button>

        <button id="delete-preset-btn" class="px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm" disabled>
            Delete
        </button>
    </div>

    <!-- Status Message -->
    <div id="preset-status" class="mt-2 text-sm hidden"></div>
</div>

<!-- Hidden file input for import -->
<input type="file" id="preset-import-input" accept=".yaml,.yml" style="display: none;">
```

### Modal Dialog: Save Preset

```html
<!-- Save Preset Modal -->
<div id="save-preset-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl p-6 max-w-md w-full">
        <h3 class="text-xl font-bold mb-4">Save as Preset</h3>

        <div class="mb-4">
            <label class="block text-sm font-medium mb-1">Preset Name *</label>
            <input type="text" id="preset-name-input"
                   class="w-full border rounded px-3 py-2"
                   placeholder="My Custom Style"
                   maxlength="50">
            <p class="text-xs text-gray-500 mt-1">Letters, numbers, spaces, dashes, and underscores only</p>
        </div>

        <div class="mb-4">
            <label class="block text-sm font-medium mb-1">Description (optional)</label>
            <textarea id="preset-description-input"
                      class="w-full border rounded px-3 py-2"
                      placeholder="Brief description of this preset"
                      rows="3"></textarea>
        </div>

        <div class="flex justify-end gap-2">
            <button id="save-preset-cancel" class="px-4 py-2 border rounded hover:bg-gray-100">
                Cancel
            </button>
            <button id="save-preset-confirm" class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
                Save
            </button>
        </div>
    </div>
</div>
```

### JavaScript Frontend Logic

```javascript
// Preset management
let currentPresets = { factory: [], user: [] };
let selectedPreset = null;

// Load presets on page load
async function loadPresets() {
    const response = await fetch('/api/presets');
    currentPresets = await response.json();
    updatePresetDropdown();
}

function updatePresetDropdown() {
    const selector = document.getElementById('preset-selector');
    const factoryGroup = selector.querySelector('optgroup[label="Factory Presets"]');
    const userGroup = selector.querySelector('optgroup[label="My Presets"]');

    // Clear existing options
    factoryGroup.innerHTML = '';
    userGroup.innerHTML = '';

    // Add factory presets
    currentPresets.factory.forEach(preset => {
        const option = document.createElement('option');
        option.value = preset.slug;
        option.textContent = preset.name;
        option.dataset.description = preset.description;
        factoryGroup.appendChild(option);
    });

    // Add user presets
    currentPresets.user.forEach(preset => {
        const option = document.createElement('option');
        option.value = preset.slug;
        option.textContent = preset.name;
        option.dataset.description = preset.description;
        userGroup.appendChild(option);
    });
}

// Load preset button
document.getElementById('load-preset-btn').addEventListener('click', async () => {
    const selector = document.getElementById('preset-selector');
    const slug = selector.value;

    if (!slug) {
        showStatus('Please select a preset', 'error');
        return;
    }

    // Warn if unsaved changes
    if (hasUnsavedChanges) {
        if (!confirm('You have unsaved changes. Loading a preset will discard them. Continue?')) {
            return;
        }
    }

    try {
        const response = await fetch(`/api/presets/load/${slug}`, { method: 'POST' });
        const data = await response.json();

        if (data.status === 'success') {
            // Update all form fields with loaded config
            applyConfigToForm(data.config);

            // Update saved config state
            savedConfig = data.config;
            hasUnsavedChanges = false;

            showStatus(`Preset "${selector.options[selector.selectedIndex].text}" loaded`, 'success');
            updateAllFieldIndicators();
        } else {
            showStatus(data.error, 'error');
        }
    } catch (error) {
        showStatus('Failed to load preset', 'error');
    }
});

// Save preset button
document.getElementById('save-preset-btn').addEventListener('click', () => {
    document.getElementById('save-preset-modal').classList.remove('hidden');
    document.getElementById('preset-name-input').focus();
});

// Save preset confirm
document.getElementById('save-preset-confirm').addEventListener('click', async () => {
    const name = document.getElementById('preset-name-input').value.trim();
    const description = document.getElementById('preset-description-input').value.trim();

    if (!name) {
        alert('Please enter a preset name');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('description', description);

        const response = await fetch('/api/presets/save', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.status === 'success') {
            showStatus(`Preset "${name}" saved`, 'success');
            loadPresets(); // Refresh preset list

            // Close modal and clear inputs
            document.getElementById('save-preset-modal').classList.add('hidden');
            document.getElementById('preset-name-input').value = '';
            document.getElementById('preset-description-input').value = '';
        } else {
            alert(data.error);
        }
    } catch (error) {
        alert('Failed to save preset');
    }
});

// Export preset button
document.getElementById('export-preset-btn').addEventListener('click', () => {
    const selector = document.getElementById('preset-selector');
    const slug = selector.value;

    if (!slug) {
        showStatus('Please select a preset to export', 'error');
        return;
    }

    // Trigger download
    window.location.href = `/api/presets/export/${slug}`;
    showStatus('Preset exported', 'success');
});

// Import preset button
document.getElementById('import-preset-btn').addEventListener('click', () => {
    document.getElementById('preset-import-input').click();
});

document.getElementById('preset-import-input').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/presets/import', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.status === 'success') {
            showStatus(`Preset "${data.preset.name}" imported`, 'success');
            loadPresets(); // Refresh preset list
        } else {
            alert(data.error);
        }
    } catch (error) {
        alert('Failed to import preset');
    }

    // Reset file input
    e.target.value = '';
});

// Delete preset button
document.getElementById('delete-preset-btn').addEventListener('click', async () => {
    const selector = document.getElementById('preset-selector');
    const slug = selector.value;

    if (!slug) return;

    const presetName = selector.options[selector.selectedIndex].text;

    if (!confirm(`Are you sure you want to delete the preset "${presetName}"? This cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/presets/delete/${slug}`, { method: 'DELETE' });
        const data = await response.json();

        if (data.status === 'success') {
            showStatus(`Preset "${presetName}" deleted`, 'success');
            loadPresets(); // Refresh preset list
            selector.value = ''; // Clear selection
        } else {
            alert(data.error);
        }
    } catch (error) {
        alert('Failed to delete preset');
    }
});

// Enable/disable delete button based on selection
document.getElementById('preset-selector').addEventListener('change', (e) => {
    const slug = e.target.value;
    const deleteBtn = document.getElementById('delete-preset-btn');

    if (!slug) {
        deleteBtn.disabled = true;
        return;
    }

    // Check if it's a user preset (can delete)
    const isUserPreset = currentPresets.user.some(p => p.slug === slug);
    deleteBtn.disabled = !isUserPreset;
});

function showStatus(message, type) {
    const statusEl = document.getElementById('preset-status');
    statusEl.textContent = message;
    statusEl.className = `mt-2 text-sm ${type === 'error' ? 'text-red-600' : 'text-green-600'}`;
    statusEl.classList.remove('hidden');

    setTimeout(() => {
        statusEl.classList.add('hidden');
    }, 3000);
}

function applyConfigToForm(config) {
    // Update all form fields with config values
    document.getElementById('prose_size').value = config.prose_size || 'prose';
    document.getElementById('prose_color').value = config.prose_color || '';
    document.getElementById('codehilite_theme').value = config.codehilite_theme || 'default';

    // Codehilite container
    document.getElementById('codehilite_auto_bg').checked = config.codehilite_container.auto_background;
    document.getElementById('codehilite_custom_bg').value = config.codehilite_container.custom_background || '';
    document.getElementById('codehilite_wrapper_classes').value = config.codehilite_container.wrapper_classes || '';

    // Custom classes (all 22 elements)
    Object.keys(config.custom_classes).forEach(element => {
        const input = document.getElementById(`${element}_classes`);
        if (input) {
            input.value = config.custom_classes[element] || '';
        }
    });
}

// Initialize presets on page load
loadPresets();
```

---

## Implementation Roadmap

### Phase 1: Backend Foundation (1-1.5 hours)

**Task 1.1**: Create preset directory structure
- Add directory creation to `PDFGenerator.__init__()`
- Create factory and user subdirectories
- **Files**: `pdf_generator.py:27-35`

**Task 1.2**: Add validation function
- Implement `validate_preset_name()` helper
- Add security checks (path traversal, etc.)
- **Files**: New helper in `pdf_generator.py`

**Task 1.3**: Implement preset CRUD methods
- `save_preset()` - Save current config as preset
- `load_preset()` - Load and apply preset
- `delete_preset()` - Remove user preset
- `list_presets()` - Enumerate all presets
- `_load_preset_metadata()` - Extract metadata
- **Files**: `pdf_generator.py:150-250` (new methods)

**Task 1.4**: Create factory presets
- `_get_minimal_config()` - Minimal styling
- `_get_academic_config()` - Formal/academic
- `_get_dark_mode_config()` - Dark theme
- `_create_factory_presets()` - Generate on first run
- **Files**: `pdf_generator.py:250-320`

---

### Phase 2: API Routes (1 hour)

**Task 2.1**: List presets endpoint
- `GET /api/presets` - Return factory + user presets
- **Files**: `main.py` (new route)

**Task 2.2**: Save preset endpoint
- `POST /api/presets/save` - Save current config with name
- **Files**: `main.py` (new route)

**Task 2.3**: Load preset endpoint
- `POST /api/presets/load/{slug}` - Apply preset to config
- **Files**: `main.py` (new route)

**Task 2.4**: Delete preset endpoint
- `DELETE /api/presets/delete/{slug}` - Remove preset
- **Files**: `main.py` (new route)

**Task 2.5**: Export preset endpoint
- `GET /api/presets/export/{slug}` - Download preset file
- **Files**: `main.py` (new route)

**Task 2.6**: Import preset endpoint
- `POST /api/presets/import` - Upload and save preset
- **Files**: `main.py` (new route)

---

### Phase 3: Frontend UI (1-1.5 hours)

**Task 3.1**: Add presets section to settings form
- Preset selector dropdown
- Action buttons (Load, Save, Export, Import, Delete)
- **Files**: `templates/index.html:100-150`

**Task 3.2**: Create save preset modal
- Name and description inputs
- Cancel/Save buttons
- **Files**: `templates/index.html:600-650`

**Task 3.3**: Implement JavaScript logic
- `loadPresets()` - Fetch and populate dropdown
- Preset load handler with unsaved changes warning
- Save preset modal handlers
- Export/import file handling
- Delete preset confirmation
- **Files**: `templates/index.html:900-1100` (JavaScript section)

---

### Phase 4: Testing & Polish (0.5-1 hour)

**Task 4.1**: Manual testing
- [ ] Create custom preset and verify save
- [ ] Load preset and verify all fields update
- [ ] Export preset and verify download
- [ ] Import preset and verify parsing
- [ ] Delete preset and verify removal
- [ ] Test factory presets immutability
- [ ] Test unsaved changes warning
- [ ] Test preset name validation

**Task 4.2**: Edge case testing
- [ ] Very long preset names (50 char limit)
- [ ] Special characters in names
- [ ] Importing malformed YAML
- [ ] Importing preset with missing fields
- [ ] Deleting currently loaded preset
- [ ] Loading preset with unsaved changes

**Task 4.3**: Documentation
- Update `CLAUDE.md` with preset system overview
- Document preset file format in `docs/implementation-details.md`

---

## Testing Strategy

### Unit Tests (Optional)

```python
# test_presets.py
import pytest
from pdf_generator import PDFGenerator, validate_preset_name

def test_validate_preset_name():
    assert validate_preset_name("My Preset")[0] == True
    assert validate_preset_name("test-123")[0] == True
    assert validate_preset_name("")[0] == False
    assert validate_preset_name("a" * 51)[0] == False
    assert validate_preset_name("../etc/passwd")[0] == False
    assert validate_preset_name("test<script>")[0] == False

def test_save_and_load_preset():
    gen = PDFGenerator()

    # Modify config
    gen.config['prose_size'] = 'prose-xl'

    # Save as preset
    slug = gen.save_preset("Test Preset", "Test description")
    assert slug == "test-preset"

    # Reset config
    gen.config['prose_size'] = 'prose'

    # Load preset
    loaded = gen.load_preset("test-preset")
    assert loaded['prose_size'] == 'prose-xl'

    # Cleanup
    gen.delete_preset("test-preset")

def test_factory_presets_cannot_be_deleted():
    gen = PDFGenerator()

    with pytest.raises(FileNotFoundError):
        gen.delete_preset("default")
```

### Manual Testing Checklist

**Preset Creation**:
- [ ] Save current settings as "Test Preset"
- [ ] Verify preset appears in dropdown under "My Presets"
- [ ] Verify preset file exists: `~/Library/Application Support/md2pdf/presets/user/test-preset.yaml`
- [ ] Open file and verify metadata and config are correct

**Preset Loading**:
- [ ] Modify several settings
- [ ] Select "Minimal" factory preset and click Load
- [ ] Verify all form fields update to minimal values
- [ ] Verify unsaved changes warning appears if modified

**Preset Export**:
- [ ] Select a preset and click Export
- [ ] Verify file downloads with `.md2pdf-preset.yaml` extension
- [ ] Open file in text editor and verify valid YAML

**Preset Import**:
- [ ] Click Import and select exported preset file
- [ ] Verify preset appears in dropdown
- [ ] Test importing malformed YAML (should show error)

**Preset Deletion**:
- [ ] Select user preset and click Delete
- [ ] Confirm deletion dialog
- [ ] Verify preset removed from dropdown
- [ ] Verify file deleted from filesystem
- [ ] Try to delete factory preset (button should be disabled)

**Edge Cases**:
- [ ] Create preset with 50 character name (max length)
- [ ] Try to create preset with 51 characters (should fail)
- [ ] Try preset name with special characters `!@#$%` (should fail)
- [ ] Import preset with missing fields (should fail with clear error)
- [ ] Load preset while unsaved changes exist (should warn)

---

## Risk Assessment & Mitigation

### Risk 1: File System Permissions
**Risk**: Users may not have write access to `~/Library/Application Support/`
**Likelihood**: Low (standard on macOS)
**Impact**: High (feature completely broken)
**Mitigation**:
- Add error handling with clear message
- Fall back to project directory if Application Support fails
- Log permission errors for debugging

### Risk 2: Preset Name Collisions
**Risk**: User tries to save preset with existing name
**Likelihood**: Medium
**Impact**: Low (overwrites without warning)
**Mitigation**:
- Check for existing preset before saving
- Show confirmation dialog if overwrite needed
- Add "last modified" timestamp to metadata

### Risk 3: Malicious Preset Import
**Risk**: User imports malicious YAML with code injection
**Likelihood**: Low (requires malicious file)
**Impact**: High (code execution)
**Mitigation**:
- Use `yaml.safe_load()` instead of `yaml.load()`
- Validate all config values against schema
- Sanitize preset names before filesystem operations

### Risk 4: Backwards Compatibility
**Risk**: Existing `config.yaml` breaks with new preset system
**Likelihood**: Low (additive changes only)
**Impact**: Medium (user loses settings)
**Mitigation**:
- Preset system is additive (doesn't modify existing config structure)
- Migration logic in `load_config()` handles missing fields
- Factory reset still available as fallback

---

## Dependencies & Prerequisites

### Required
- Python 3.8+ (already required)
- PyYAML (already installed)
- FastAPI (already installed)

### Optional
- None

### System Requirements
- Write access to `~/Library/Application Support/md2pdf/`
- ~1MB disk space for presets directory

---

## Future Enhancements (Post-MVP)

### V2 Features
1. **Preset Preview**: Show sample markdown with preset applied before loading
2. **Preset Versioning**: Track preset modification history
3. **Preset Tags**: Categorize presets (work, personal, academic, etc.)
4. **Preset Search**: Filter presets by name/description/tags
5. **Batch Preset Export**: Export all presets as ZIP
6. **Cloud Sync**: Sync presets across devices via cloud storage

### Integration Ideas
- **CLI Support**: `md2pdf --preset academic input.md output.pdf`
- **Preset Marketplace**: Community-shared presets
- **AI Preset Generator**: Generate presets from natural language descriptions

---

## Success Metrics (Post-Launch)

**Adoption Metrics**:
- % of users who create at least 1 custom preset (target: 60%)
- Average number of presets per active user (target: 3-5)
- Factory preset usage breakdown (which are most popular)

**Engagement Metrics**:
- Preset load operations per session (target: 2-3)
- Preset export/import usage (indicator of team collaboration)
- Time saved vs manual reconfiguration (estimated 30-60 seconds per switch)

**Quality Metrics**:
- Preset-related error rate (target: <1%)
- User-reported issues with preset system (target: <5 reports)

---

## Appendix: Factory Preset Specifications

### Preset 1: Factory Default
**File**: `presets/factory/default.yaml`
**Description**: Original MD2PDF default styling
**Config**: `PDFGenerator.get_default_config()` output

### Preset 2: Minimal
**File**: `presets/factory/minimal.yaml`
**Description**: Clean, minimal styling with no custom classes
**Changes from default**:
- `prose_size: prose-sm`
- All `custom_classes` set to empty strings

### Preset 3: Academic
**File**: `presets/factory/academic.yaml`
**Description**: Formal styling for research papers and academic documents
**Changes from default**:
```yaml
prose_size: prose-lg
prose_color: prose-slate
custom_classes:
  h1: "text-4xl font-bold text-gray-900 border-b-2 border-gray-300 pb-2"
  h2: "text-3xl font-semibold text-gray-800 mt-8 mb-3"
  h3: "text-2xl font-semibold text-gray-700"
  blockquote: "border-l-4 border-blue-500 pl-4 italic bg-blue-50 py-2"
  table: "border-collapse border border-gray-300"
  th: "bg-gray-100 font-semibold border border-gray-300 px-4 py-2"
  td: "border border-gray-300 px-4 py-2"
```

### Preset 4: Dark Mode
**File**: `presets/factory/dark-mode.yaml`
**Description**: Dark theme for reduced eye strain
**Changes from default**:
```yaml
prose_color: prose-invert
codehilite_theme: monokai
custom_classes:
  body: "bg-gray-900 text-gray-100"
  h1: "text-gray-100"
  h2: "text-gray-100"
  h3: "text-gray-100"
  a: "text-blue-400 hover:text-blue-300"
  blockquote: "border-l-4 border-blue-400 text-gray-300"
```

---

## File Locations Summary

```
Project Files:
  pdf_generator.py          → +250 lines (preset methods)
  main.py                   → +150 lines (6 new routes)
  templates/index.html      → +200 lines (UI + JavaScript)

Generated Files:
  ~/Library/Application Support/md2pdf/presets/
    factory/
      default.yaml          → Created on first run
      minimal.yaml          → Created on first run
      academic.yaml         → Created on first run
      dark-mode.yaml        → Created on first run
    user/
      {slug}.yaml           → User-created presets
```

---

**Total Estimated Effort**: 3-4 hours
**Priority**: High
**Status**: Ready for implementation
