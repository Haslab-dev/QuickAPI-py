"""
Layout system for QuickAPI templates
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class LayoutConfig:
    """Configuration for page layout"""
    title: str = "QuickAPI Template"
    meta_tags: List[Dict[str, str]] = field(default_factory=list)
    stylesheets: List[str] = field(default_factory=list)  # External CSS URLs
    custom_styles: str = ""  # Inline CSS
    tailwind_css: str = ""  # Tailwind CSS v4 styles
    scripts: List[str] = field(default_factory=list)  # External JS URLs
    custom_scripts: str = ""  # Inline JS
    body_class: str = ""
    lang: str = "en"
    charset: str = "UTF-8"
    viewport: str = "width=device-width, initial-scale=1.0"


class BaseLayout:
    """Base layout class for HTML templates"""
    
    def __init__(self, config: Optional[LayoutConfig] = None):
        self.config = config or LayoutConfig()
    
    def render_meta_tags(self) -> str:
        """Render meta tags"""
        meta_html = f'<meta charset="{self.config.charset}">\n'
        meta_html += f'<meta name="viewport" content="{self.config.viewport}">\n'
        
        for meta in self.config.meta_tags:
            attrs = ' '.join(f'{k}="{v}"' for k, v in meta.items())
            meta_html += f'<meta {attrs}>\n'
        
        return meta_html
    
    def render_stylesheets(self) -> str:
        """Render external stylesheets"""
        css_html = ""
        for stylesheet in self.config.stylesheets:
            css_html += f'<link rel="stylesheet" href="{stylesheet}">\n'
        return css_html
    
    def render_custom_styles(self) -> str:
        """Render custom inline styles"""
        if self.config.custom_styles:
            return f"<style>\n{self.config.custom_styles}\n</style>\n"
        return ""
    
    def render_tailwind_styles(self, tailwind_css: str = "") -> str:
        """Render Tailwind CSS v4 styles"""
        if tailwind_css:
            return f'<style type="text/tailwindcss">\n{tailwind_css}\n</style>\n'
        return ""
    
    def render_scripts(self) -> str:
        """Render external scripts"""
        js_html = ""
        for script in self.config.scripts:
            js_html += f'<script src="{script}"></script>\n'
        return js_html
    
    def render_custom_scripts(self) -> str:
        """Render custom inline scripts"""
        if self.config.custom_scripts:
            return f"<script>\n{self.config.custom_scripts}\n</script>\n"
        return ""
    
    def render_head(self, additional_head_content: str = "") -> str:
        """Render the complete head section"""
        return f"""<head>
    {self.render_meta_tags()}
    <title>{self.config.title}</title>
    {self.render_stylesheets()}
    {self.render_tailwind_styles(self.config.tailwind_css)}
    {self.render_custom_styles()}
    {additional_head_content}
</head>"""
    
    def render_body_start(self) -> str:
        """Render the body opening tag"""
        body_class = f' class="{self.config.body_class}"' if self.config.body_class else ""
        return f"<body{body_class}>"
    
    def render_body_end(self, additional_scripts: str = "") -> str:
        """Render the body closing with scripts"""
        return f"""    {self.render_scripts()}
    {self.render_custom_scripts()}
    {additional_scripts}
</body>"""
    
    def render(self, content: str, additional_head_content: str = "", additional_scripts: str = "") -> str:
        """Render the complete HTML page"""
        return f"""<!DOCTYPE html>
<html lang="{self.config.lang}">
{self.render_head(additional_head_content)}
{self.render_body_start()}
    {content}
{self.render_body_end(additional_scripts)}
</html>"""


class DefaultLayout(BaseLayout):
    """Default layout with basic styling"""
    
    def __init__(self, config: Optional[LayoutConfig] = None):
        if config is None:
            config = LayoutConfig()
        
        # Add default styles if none provided
        if not config.custom_styles:
            config.custom_styles = """
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            padding: 20px;
            line-height: 1.6;
        }
        button {
            margin: 5px;
            padding: 8px 16px;
            cursor: pointer;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: #f8f9fa;
        }
        button:hover {
            background: #e9ecef;
        }
        input, textarea, select {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 5px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        """
        
        super().__init__(config)


class MinimalLayout(BaseLayout):
    """Minimal layout with no default styling"""
    
    def __init__(self, config: Optional[LayoutConfig] = None):
        super().__init__(config or LayoutConfig())


# Layout presets
def create_bootstrap_layout(title: str = "QuickAPI Template") -> BaseLayout:
    """Create a layout with Bootstrap CSS framework"""
    config = LayoutConfig(
        title=title,
        stylesheets=[
            "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
        ],
        scripts=[
            "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"
        ]
    )
    return BaseLayout(config)


def create_tailwind_layout(title: str = "QuickAPI Template", custom_theme: str = "") -> BaseLayout:
    """Create a layout with Tailwind CSS v4 browser framework"""
    
    # Default Tailwind theme configuration
    default_theme = """
@theme {
  --color-primary: #3b82f6;
  --color-secondary: #6b7280;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  --color-info: #06b6d4;
}
"""
    
    config = LayoutConfig(
        title=title,
        scripts=[
            "https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"
        ],
        tailwind_css=custom_theme or default_theme
    )
    return BaseLayout(config)


def create_custom_layout(
    title: str = "QuickAPI Template",
    stylesheets: List[str] = None,
    scripts: List[str] = None,
    custom_styles: str = "",
    custom_scripts: str = ""
) -> BaseLayout:
    """Create a custom layout with specified resources"""
    config = LayoutConfig(
        title=title,
        stylesheets=stylesheets or [],
        scripts=scripts or [],
        custom_styles=custom_styles,
        custom_scripts=custom_scripts
    )
    return BaseLayout(config)