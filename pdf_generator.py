import markdown
from markdown.extensions import tables, fenced_code, codehilite
import yaml
from pathlib import Path
from typing import Dict, Optional
import io
import os

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

        self.config_path = config_path
        self.config = self.load_config(config_path)
        self.weasyprint_available = None
        self.font_config = None
        
    def _check_dependencies(self):
        if self.weasyprint_available is not None:
            return self.weasyprint_available
            
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            self.weasyprint_available = True
            self.font_config = FontConfiguration()
        except (ImportError, OSError) as e:
            self.weasyprint_available = False
            print(f"Warning: WeasyPrint not available - {e}")
            print("Please install system dependencies. See README.md for instructions.")
            return False
        return True
        
    def load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    @staticmethod
    def get_default_config():
        """Return default config structure"""
        return {
            'prose_size': 'prose',
            'prose_color': '',
            'codehilite_theme': 'default',
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

            # Add container styling
            container_css = """
.codehilite {
    background: #f8f8f8;
    padding: 1em;
    border-radius: 0.5em;
    overflow-x: auto;
    margin: 1em 0;
}
"""
            full_css = container_css + css

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
                    'pygments_style': theme_name
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
    
    def generate_full_html(self, markdown_content: str, use_external_css: bool = True) -> str:
        html_body = self.markdown_to_html(markdown_content)
        html_body = self.apply_custom_classes(html_body)
        
        prose_size = self.config['prose_size']
        
        # Choose CSS approach based on PDF generator
        css_link = ""
        if use_external_css:
            css_link = '<link href="https://cdn.jsdelivr.net/npm/tailwindcss@3.4.0/dist/tailwind.min.css" rel="stylesheet">'
        
        full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {css_link}
    <style>
        @page {{
            size: {self.config['pdf_options']['format']};
            margin: {self.config['pdf_options']['margin_top']}
                    {self.config['pdf_options']['margin_right']}
                    {self.config['pdf_options']['margin_bottom']}
                    {self.config['pdf_options']['margin_left']};
        }}
    </style>
</head>
<body class="bg-white">
    <div class="prose {prose_size} max-w-none p-8">
        {html_body}
    </div>
</body>
</html>
"""
        return full_html
    
    def generate_pdf(self, markdown_content: str, output_path: Optional[str] = None) -> bytes:
        # Try WeasyPrint first
        if self._check_dependencies():
            try:
                from weasyprint import HTML
                html_content = self.generate_full_html(markdown_content, use_external_css=True)
                if output_path:
                    HTML(string=html_content).write_pdf(
                        output_path,
                        font_config=self.font_config
                    )
                    with open(output_path, 'rb') as f:
                        return f.read()
                else:
                    pdf_bytes = HTML(string=html_content).write_pdf(
                        font_config=self.font_config
                    )
                    return pdf_bytes
            except Exception as e:
                print(f"WeasyPrint failed: {e}")
                # Fall through to xhtml2pdf
        
        # Fallback to xhtml2pdf (without external CSS)
        print("Using xhtml2pdf as fallback PDF generator...")
        from xhtml2pdf import pisa
        
        html_content = self.generate_full_html(markdown_content, use_external_css=False)
        
        if output_path:
            with open(output_path, "wb") as result_file:
                pisa_status = pisa.CreatePDF(html_content, dest=result_file)
                if pisa_status.err:
                    raise RuntimeError(f"xhtml2pdf error: {pisa_status.err}")
            with open(output_path, 'rb') as f:
                return f.read()
        else:
            result = io.BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=result)
            if pisa_status.err:
                raise RuntimeError(f"xhtml2pdf error: {pisa_status.err}")
            return result.getvalue()