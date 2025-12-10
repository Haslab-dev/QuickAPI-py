"""
Template response for the templating engine
"""

from typing import Dict, Any, Optional
from ..response import HTMLResponse
from .layout import BaseLayout, DefaultLayout


class TemplateResponse(HTMLResponse):
    """Response for rendering templates with client-side JavaScript"""
    
    def __init__(self, template_engine, layout: Optional[BaseLayout] = None, status_code: int = 200, headers: Optional[Dict[str, str]] = None):
        self.template_engine = template_engine
        self.layout = layout or DefaultLayout()
        
        # Generate the HTML with embedded JavaScript
        html_content = self._generate_html()
        
        super().__init__(html_content, status_code, headers)
    
    def _generate_html(self) -> str:
        """Generate the complete HTML page with embedded JavaScript"""
        # Render the component to HTML
        if self.template_engine.root_component:
            content_html = self.template_engine.root_component.render().to_html()
            component_id = self.template_engine.root_component.id
            initial_state = getattr(self.template_engine.root_component.hook_context, 'states', {})
        else:
            content_html = "<div>No content</div>"
            component_id = None
            initial_state = {}
        
        # Build the reactive system JavaScript
        reactive_script = self._build_reactive_script(component_id, initial_state)
        
        # Wrap content in root div
        body_content = f'<div id="root">\n    {content_html}\n</div>'
        
        # Use layout to render the complete page
        return self.layout.render(
            content=body_content,
            additional_scripts=f"<script>\n{reactive_script}\n</script>"
        )
    
    def _build_reactive_script(self, component_id: Any, initial_state: Dict[str, Any]) -> str:
        """Build the reactive system JavaScript"""
        return f"""
        // QuickAPI Reactive System
        class QuickAPIReactive {{
            constructor(componentId, initialState) {{
                this.componentId = componentId;
                this.state = initialState || {{}};
                this.setupEventListeners();
            }}
            
            setState(key, value) {{
                this.state[key] = value;
                this.updateDOM();
            }}
            
            updateDOM() {{
                // Update text content for elements with data-bind attribute
                document.querySelectorAll('[data-bind]').forEach(el => {{
                    const bindKey = el.getAttribute('data-bind');
                    if (this.state.hasOwnProperty(bindKey)) {{
                        el.textContent = this.state[bindKey];
                    }}
                }});
            }}
            
            setupEventListeners() {{
                // Setup click handlers for elements with data-action or data-handler attributes
                document.addEventListener('click', (e) => {{
                    const action = e.target.getAttribute('data-action');
                    const handler = e.target.getAttribute('data-handler');
                    
                    if (action) {{
                        e.preventDefault();
                        this.handleAction(action);
                    }} else if (handler) {{
                        e.preventDefault();
                        this.executeHandler(handler);
                    }}
                }});
            }}
            
            handleAction(action) {{
                try {{
                    // Create a function that can access the context
                    const func = new Function('state', 'setState', action);
                    
                    // Execute the action with context
                    func(this.state, (key, value) => this.setState(key, value));
                }} catch (error) {{
                    console.error('Action execution error:', error);
                }}
            }}
            
            async executeHandler(handlerId) {{
                try {{
                    const response = await fetch('/rpc', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            method: 'execute_handler',
                            params: {{
                                handlerId: handlerId,
                                componentId: this.componentId
                            }}
                        }})
                    }});
                    
                    const result = await response.json();
                    if (result.result && result.result.success) {{
                        // Handler executed successfully, component will re-render
                        console.log('Handler executed successfully');
                    }} else {{
                        console.error('Handler execution failed:', result.result?.error);
                    }}
                }} catch (error) {{
                    console.error('Handler execution error:', error);
                }}
            }}
        }}
        
        // Initialize reactive system
        const reactive = new QuickAPIReactive('{component_id}', {self._escape_json(initial_state)});
        console.log('QuickAPI Reactive System loaded');
        """
    
    def _escape_json(self, data: Any) -> str:
        """Escape data for embedding in HTML"""
        import json
        return json.dumps(data).replace('</script>', '<\\/script>')