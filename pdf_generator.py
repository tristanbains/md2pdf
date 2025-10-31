import markdown
from markdown.extensions import tables, fenced_code, codehilite
import yaml
from pathlib import Path
from typing import Dict, Optional
import os
import re
from datetime import datetime

class PDFGenerator:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Check for config in Application Support (for distributed app)
            app_support = os.path.expanduser("~/Library/Application Support/md2pdf")
            app_config_path = os.path.join(app_support, "config.yaml")

            if os.path.exists(app_config_path):
                config_path = app_config_path
            elif os.path.exists("config.yaml"):
                # Development mode - use local config
                config_path = "config.yaml"
            else:
                # Create default config in Application Support
                os.makedirs(app_support, exist_ok=True)
                config_path = app_config_path
                self._create_default_config(config_path)

        self.config_path = Path(config_path)
        self.config = self.load_config(config_path)

        # Set up preset directories
        self.presets_dir = self.config_path.parent / "presets"
        self.factory_presets_dir = self.presets_dir / "factory"
        self.user_presets_dir = self.presets_dir / "user"
        self._ensure_presets_directory()

    def load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Migrate old configs: add codehilite_container if missing
        if 'codehilite_container' not in config:
            default_config = self.get_default_config()
            config['codehilite_container'] = default_config['codehilite_container']
            # Save updated config
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

        return config

    @staticmethod
    def get_default_config():
        """Return default config structure"""
        return {
            'prose_size': 'prose',
            'prose_color': 'prose-slate',
            'codehilite_theme': 'github-dark',
            'codehilite_container': {
                'auto_background': True,
                'custom_background': '',
                'wrapper_classes': 'p-4 rounded-lg overflow-x-auto my-4'
            },
            'custom_classes': {
                'a': '',
                'blockquote': '',
                'code': '',
                'h1': '',
                'h2': '',
                'h3': '',
                'h4': '',
                'h5': '',
                'h6': '',
                'hr': '',
                'img': '',
                'li': '',
                'ol': '',
                'p': '',
                'pre': '',
                'table': '',
                'thead': '',
                'tbody': '',
                'tr': '',
                'td': '',
                'th': '',
                'ul': ''
            },
            'pdf_options': {
                'format': 'A4',
                'margin_bottom': '20mm',
                'margin_left': '20mm',
                'margin_right': '20mm',
                'margin_top': '20mm',
                'orientation': 'portrait'
            }
        }

    def _create_default_config(self, path: str):
        """Create default config file with academic preset"""
        default_config = self.get_default_config()
        with open(path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)

    def save_config(self, config_path: str = None):
        if config_path is None:
            config_path = self.config_path
        with open(config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def update_config(self, updates: Dict):
        if 'prose_size' in updates:
            self.config['prose_size'] = updates['prose_size']
        if 'prose_color' in updates:
            self.config['prose_color'] = updates['prose_color']
        if 'codehilite_theme' in updates:
            self.config['codehilite_theme'] = updates['codehilite_theme']
        if 'codehilite_container' in updates:
            # Ensure codehilite_container exists in config
            if 'codehilite_container' not in self.config:
                self.config['codehilite_container'] = self.get_default_config()['codehilite_container']
            self.config['codehilite_container'].update(updates['codehilite_container'])
        if 'custom_classes' in updates:
            self.config['custom_classes'].update(updates['custom_classes'])
        self.save_config()

    def get_codehilite_css(self, theme_name: str = None, scope_prefix: str = None) -> str:
        """Generate CSS for code highlighting from Pygments theme

        Args:
            theme_name: Name of the Pygments theme to use
            scope_prefix: Optional CSS class prefix to scope the styles (e.g., '.theme-monokai')
        """
        from pygments.formatters import HtmlFormatter
        import re

        if theme_name is None:
            theme_name = self.config.get('codehilite_theme', 'default')

        try:
            formatter = HtmlFormatter(style=theme_name)
            css = formatter.get_style_defs('.codehilite')

            # Extract background color from the theme
            background = getattr(formatter.style, 'background_color', None)
            if not background:
                background = '#f6f8fa'  # Light gray fallback

            # Add rules to ensure nested elements match the wrapper background
            # This prevents TailwindCSS Typography from applying conflicting backgrounds
            additional_css = f"""
.codehilite pre {{ background-color: {background} !important; }}
.codehilite code {{ background-color: transparent; }}
"""

            full_css = css + additional_css

            # If scope_prefix provided, prepend it to all selectors
            if scope_prefix:
                # Remove trailing/leading whitespace from prefix
                scope_prefix = scope_prefix.strip()

                # Match CSS selectors (everything before the opening brace)
                # This regex finds patterns like ".codehilite .k {" or ".codehilite {"
                def add_scope(match):
                    selector = match.group(1).strip()
                    # Prepend scope prefix to the selector
                    return f"{scope_prefix} {selector} {{"

                # Replace all CSS selectors with scoped versions
                full_css = re.sub(r'([^{}]+)\s*\{', add_scope, full_css)

            return full_css
        except Exception as e:
            print(f"Error generating CSS for theme '{theme_name}': {e}")
            # Fallback to default theme
            formatter = HtmlFormatter(style='default')
            return formatter.get_style_defs('.codehilite')

    @staticmethod
    def get_available_themes():
        """Get list of all available Pygments themes"""
        from pygments.styles import get_all_styles
        return sorted(list(get_all_styles()))
    
    def markdown_to_html(self, markdown_content: str) -> str:
        # Get configured theme
        theme_name = self.config.get('codehilite_theme', 'default')

        md = markdown.Markdown(
            extensions=[
                'tables',
                'fenced_code',
                'codehilite',
                'nl2br',
                'sane_lists',
                'attr_list',
                'def_list',
                'abbr',
                'footnotes',
                'toc'
            ],
            extension_configs={
                'codehilite': {
                    'pygments_style': theme_name,
                    'noclasses': False  # Generate CSS classes instead of inline styles
                }
            }
        )
        return md.convert(markdown_content)
    
    def apply_custom_classes(self, html_content: str) -> str:
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            custom_classes = self.config.get('custom_classes', {})

            if not isinstance(custom_classes, dict):
                print(f"WARNING: custom_classes is not a dict: {type(custom_classes)}")
                return html_content

            for tag, classes in custom_classes.items():
                if classes and isinstance(classes, str):
                    try:
                        for element in soup.find_all(tag):
                            existing_classes = element.get('class', [])
                            if isinstance(existing_classes, str):
                                existing_classes = existing_classes.split()
                            new_classes = classes.split()
                            element['class'] = existing_classes + new_classes
                    except Exception as e:
                        print(f"ERROR applying classes to {tag}: {e}")
                        continue  # Skip this tag and continue with others

            result = str(soup)
            if not isinstance(result, str):
                print(f"WARNING: soup conversion returned non-string: {type(result)}")
                return html_content  # Return original if conversion fails
            return result
        except Exception as e:
            print(f"ERROR in apply_custom_classes: {e}")
            import traceback
            traceback.print_exc()
            return html_content  # Return original HTML on error

    def apply_codehilite_wrapper_styling(self, html_content: str) -> str:
        """Apply Tailwind classes and background color to .codehilite wrapper divs"""
        from bs4 import BeautifulSoup
        from pygments.formatters import HtmlFormatter
        import re

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            container_config = self.config.get('codehilite_container', {})

            # Get wrapper classes
            wrapper_classes = container_config.get('wrapper_classes', '').strip()

            # Get background color settings
            auto_bg = container_config.get('auto_background', True)
            custom_bg = container_config.get('custom_background', '').strip()

            # Determine background color
            background = None
            if custom_bg:
                background = custom_bg
            elif auto_bg:
                theme_name = self.config.get('codehilite_theme', 'default')
                try:
                    formatter = HtmlFormatter(style=theme_name)

                    # Method 1: Direct attribute access (works for most themes)
                    background = getattr(formatter.style, 'background_color', None)

                    # Method 2: CSS parsing fallback (extracts from generated CSS)
                    if not background:
                        css = formatter.get_style_defs('.codehilite')
                        # Match background or background-color in .codehilite rule
                        css_match = re.search(
                            r'\.codehilite\s*\{[^}]*background(?:-color)?:\s*([#\w]+)',
                            css
                        )
                        if css_match:
                            background = css_match.group(1)

                    # Final fallback if both methods fail
                    if not background:
                        background = '#f6f8fa'  # Light gray fallback

                except Exception as e:
                    print(f'Warning: Could not extract background for theme "{theme_name}": {e}')
                    background = '#f6f8fa'

            # Find all .codehilite divs and apply styling
            for div in soup.find_all('div', class_='codehilite'):
                # Add Tailwind classes
                if wrapper_classes:
                    existing_classes = div.get('class', [])
                    if isinstance(existing_classes, str):
                        existing_classes = existing_classes.split()
                    new_classes = wrapper_classes.split()
                    div['class'] = existing_classes + new_classes

                # Add inline background style
                if background:
                    existing_style = div.get('style', '')
                    if existing_style and not existing_style.endswith(';'):
                        existing_style += ';'
                    div['style'] = f"{existing_style}background-color: {background};"

            return str(soup)
        except Exception as e:
            print(f"ERROR in apply_codehilite_wrapper_styling: {e}")
            import traceback
            traceback.print_exc()
            return html_content  # Return original HTML on error

    # ========== PRESET MANAGEMENT METHODS ==========

    def _ensure_presets_directory(self):
        """Create presets directory structure if it doesn't exist"""
        self.factory_presets_dir.mkdir(parents=True, exist_ok=True)
        self.user_presets_dir.mkdir(parents=True, exist_ok=True)
        self._create_factory_presets()

    def _create_factory_presets(self):
        """Create built-in factory presets if they don't exist"""
        factory_presets = {
            'default': self._get_factory_default_config(),
            'minimal': self._get_minimal_config(),
            'academic': self._get_academic_config(),
            'dark-mode': self._get_dark_mode_config()
        }

        for name, config in factory_presets.items():
            preset_path = self.factory_presets_dir / f"{name}.yaml"
            if not preset_path.exists():
                with open(preset_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)

    @staticmethod
    def _get_factory_default_config() -> dict:
        """Factory preset: default MD2PDF styling"""
        config = PDFGenerator.get_default_config()
        config['_metadata'] = {
            'name': 'Factory Default',
            'description': 'Original MD2PDF default styling with readable text',
            'is_factory': True
        }
        # Ensure proper defaults
        config['prose_color'] = 'prose-slate'
        config['codehilite_theme'] = 'github-dark'
        return config

    @staticmethod
    def _get_minimal_config() -> dict:
        """Factory preset: minimal styling"""
        config = PDFGenerator.get_default_config()
        config['_metadata'] = {
            'name': 'Minimal',
            'description': 'Clean, minimal styling with no custom classes',
            'is_factory': True
        }
        config['prose_size'] = 'prose-sm'
        config['prose_color'] = 'prose-gray'
        config['codehilite_theme'] = 'default'
        config['custom_classes'] = {k: '' for k in config['custom_classes']}
        return config

    @staticmethod
    def _get_academic_config() -> dict:
        """Factory preset: academic/formal styling"""
        config = PDFGenerator.get_default_config()
        config['_metadata'] = {
            'name': 'Academic',
            'description': 'Formal styling for research papers and academic documents',
            'is_factory': True
        }
        config['prose_size'] = 'prose-lg'
        config['prose_color'] = 'prose-slate'
        config['codehilite_theme'] = 'tango'
        config['custom_classes']['h1'] = 'text-4xl font-bold text-gray-900 border-b-2 border-gray-300 pb-2'
        config['custom_classes']['h2'] = 'text-3xl font-semibold text-gray-800 mt-8 mb-3'
        config['custom_classes']['h3'] = 'text-2xl font-semibold text-gray-700'
        config['custom_classes']['blockquote'] = 'border-l-4 border-blue-500 pl-4 italic bg-blue-50 py-2'
        config['custom_classes']['table'] = 'border-collapse border border-gray-300'
        config['custom_classes']['th'] = 'bg-gray-100 font-semibold border border-gray-300 px-4 py-2'
        config['custom_classes']['td'] = 'border border-gray-300 px-4 py-2'
        return config

    @staticmethod
    def _get_dark_mode_config() -> dict:
        """Factory preset: dark theme"""
        config = PDFGenerator.get_default_config()
        config['_metadata'] = {
            'name': 'Dark Mode',
            'description': 'Dark theme for reduced eye strain',
            'is_factory': True
        }
        config['prose_color'] = 'prose-invert'
        config['codehilite_theme'] = 'monokai'
        config['custom_classes']['h1'] = 'text-gray-100'
        config['custom_classes']['h2'] = 'text-gray-100'
        config['custom_classes']['h3'] = 'text-gray-100'
        config['custom_classes']['a'] = 'text-blue-400 hover:text-blue-300'
        config['custom_classes']['blockquote'] = 'border-l-4 border-blue-400 text-gray-300'
        return config

    def list_presets(self) -> dict:
        """List all available presets (factory + user)"""
        factory = []
        user = []

        # Factory presets
        for preset_file in sorted(self.factory_presets_dir.glob("*.yaml")):
            preset = self._load_preset_metadata(preset_file)
            preset['is_factory'] = True
            preset['can_delete'] = False
            factory.append(preset)

        # User presets
        for preset_file in sorted(self.user_presets_dir.glob("*.yaml")):
            preset = self._load_preset_metadata(preset_file)
            preset['is_factory'] = False
            preset['can_delete'] = True
            user.append(preset)

        # Sort both lists alphabetically by name (case-insensitive)
        factory.sort(key=lambda p: p['name'].lower())
        user.sort(key=lambda p: p['name'].lower())

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
        return self.save_preset_with_config(name, description, self.config)

    def save_preset_with_config(self, name: str, description: str, config: dict) -> str:
        """Save specific config as a named preset (instead of current self.config)"""
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
            **config  # Use provided config instead of self.config
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

        # Update metadata for import
        if '_metadata' not in preset_data:
            preset_data['_metadata'] = {}
        preset_data['_metadata']['name'] = name
        preset_data['_metadata']['created_at'] = datetime.now().isoformat()

        # Create slug from name
        slug = name.lower().replace(' ', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug)

        # Save as new preset
        preset_path = self.user_presets_dir / f"{slug}.yaml"
        with open(preset_path, 'w') as f:
            yaml.dump(preset_data, f, default_flow_style=False)

        return slug

    def _validate_preset_config(self, config: dict):
        """Validate preset config has required fields"""
        required_fields = ['prose_size', 'prose_color', 'codehilite_theme',
                          'codehilite_container', 'custom_classes']

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Invalid preset: missing required field '{field}'")


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