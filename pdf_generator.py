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

    def _create_default_config(self, path: str):
        """Create default config with academic preset"""
        default_config = {
            'prose_size': 'prose',
            'prose_color': '',
            'custom_classes': {
                'a': 'text-blue-600 hover:text-blue-800',
                'blockquote': 'border-l-4 border-gray-300 text-gray-600',
                'code': 'bg-gray-100 text-red-600',
                'h1': 'text-gray-900 font-bold',
                'h2': 'text-gray-800 font-semibold',
                'h3': 'text-gray-700 font-medium',
                'h4': 'text-gray-600',
                'h5': 'text-gray-600',
                'h6': 'text-gray-600',
                'hr': '',
                'img': '',
                'li': '',
                'ol': '',
                'p': 'text-gray-800',
                'pre': 'bg-gray-50 border border-gray-200',
                'table': 'border border-gray-200',
                'thead': '',
                'tbody': '',
                'tr': '',
                'td': 'border border-gray-200 px-4 py-2',
                'th': 'border border-gray-200 px-4 py-2 font-semibold bg-gray-50',
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
        if 'custom_classes' in updates:
            self.config['custom_classes'].update(updates['custom_classes'])
        self.save_config()
    
    def markdown_to_html(self, markdown_content: str) -> str:
        md = markdown.Markdown(extensions=[
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
        ])
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
        
        /* Syntax highlighting styles */
        .codehilite {{ background: #f8f8f8; padding: 1em; border-radius: 0.5em; overflow-x: auto; }}
        .codehilite .hll {{ background-color: #ffffcc }}
        .codehilite .c {{ color: #408080; font-style: italic }}
        .codehilite .k {{ color: #008000; font-weight: bold }}
        .codehilite .o {{ color: #666666 }}
        .codehilite .cm {{ color: #408080; font-style: italic }}
        .codehilite .cp {{ color: #BC7A00 }}
        .codehilite .c1 {{ color: #408080; font-style: italic }}
        .codehilite .cs {{ color: #408080; font-style: italic }}
        .codehilite .gd {{ color: #A00000 }}
        .codehilite .ge {{ font-style: italic }}
        .codehilite .gr {{ color: #FF0000 }}
        .codehilite .gh {{ color: #000080; font-weight: bold }}
        .codehilite .gi {{ color: #00A000 }}
        .codehilite .go {{ color: #888888 }}
        .codehilite .gp {{ color: #000080; font-weight: bold }}
        .codehilite .gs {{ font-weight: bold }}
        .codehilite .gu {{ color: #800080; font-weight: bold }}
        .codehilite .gt {{ color: #0044DD }}
        .codehilite .kc {{ color: #008000; font-weight: bold }}
        .codehilite .kd {{ color: #008000; font-weight: bold }}
        .codehilite .kn {{ color: #008000; font-weight: bold }}
        .codehilite .kp {{ color: #008000 }}
        .codehilite .kr {{ color: #008000; font-weight: bold }}
        .codehilite .kt {{ color: #B00040 }}
        .codehilite .m {{ color: #666666 }}
        .codehilite .s {{ color: #BA2121 }}
        .codehilite .na {{ color: #7D9029 }}
        .codehilite .nb {{ color: #008000 }}
        .codehilite .nc {{ color: #0000FF; font-weight: bold }}
        .codehilite .no {{ color: #880000 }}
        .codehilite .nd {{ color: #AA22FF }}
        .codehilite .ni {{ color: #999999; font-weight: bold }}
        .codehilite .ne {{ color: #D2413A; font-weight: bold }}
        .codehilite .nf {{ color: #0000FF }}
        .codehilite .nl {{ color: #A0A000 }}
        .codehilite .nn {{ color: #0000FF; font-weight: bold }}
        .codehilite .nt {{ color: #008000; font-weight: bold }}
        .codehilite .nv {{ color: #19177C }}
        .codehilite .ow {{ color: #AA22FF; font-weight: bold }}
        .codehilite .w {{ color: #bbbbbb }}
        .codehilite .mb {{ color: #666666 }}
        .codehilite .mf {{ color: #666666 }}
        .codehilite .mh {{ color: #666666 }}
        .codehilite .mi {{ color: #666666 }}
        .codehilite .mo {{ color: #666666 }}
        .codehilite .sb {{ color: #BA2121 }}
        .codehilite .sc {{ color: #BA2121 }}
        .codehilite .sd {{ color: #BA2121; font-style: italic }}
        .codehilite .s2 {{ color: #BA2121 }}
        .codehilite .se {{ color: #BB6622; font-weight: bold }}
        .codehilite .sh {{ color: #BA2121 }}
        .codehilite .si {{ color: #BB6688; font-weight: bold }}
        .codehilite .sx {{ color: #008000 }}
        .codehilite .sr {{ color: #BB6688 }}
        .codehilite .s1 {{ color: #BA2121 }}
        .codehilite .ss {{ color: #19177C }}
        .codehilite .bp {{ color: #008000 }}
        .codehilite .vc {{ color: #19177C }}
        .codehilite .vg {{ color: #19177C }}
        .codehilite .vi {{ color: #19177C }}
        .codehilite .il {{ color: #666666 }}
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