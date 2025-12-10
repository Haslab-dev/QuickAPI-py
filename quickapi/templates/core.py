"""
Core templating engine components
"""

import asyncio
import uuid
import json
from typing import Dict, List, Any, Callable, Optional, Union
from dataclasses import dataclass, field

from .hooks import HookContext
from .utils import get_logger

logger = get_logger(__name__)


@dataclass
class Element:
    """Represents an HTML element in the virtual DOM"""
    tag: str
    props: Dict[str, Any] = field(default_factory=dict)
    children: List['Element'] = field(default_factory=list)
    key: Optional[str] = None
    component_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert element to dictionary for serialization"""
        return {
            "tag": self.tag,
            "props": self.props,
            "children": [child.to_dict() if isinstance(child, Element) else str(child) for child in self.children],
            "key": self.key,
            "componentId": self.component_id
        }
    
    def to_html(self) -> str:
        """Convert element to HTML string"""
        # Build opening tag
        attrs = []
        for key, value in self.props.items():
            if key.startswith('on_'):
                # Handle event handlers (lambda functions or strings)
                if callable(value):
                    # Register the lambda function and create a handler ID
                    handler_id = register_event_handler(value)
                    attrs.append(f'data-handler="{handler_id}"')
                else:
                    # String-based action (legacy support)
                    attrs.append(f'data-action="{value}"')
                continue
            elif key == 'class_':
                attrs.append(f'class="{value}"')
            elif key == 'style' and isinstance(value, dict):
                style_str = '; '.join(f"{k.replace('_', '-')}: {v}" for k, v in value.items())
                attrs.append(f'style="{style_str}"')
            elif key == 'data_bind':
                # Data binding for reactive updates
                attrs.append(f'data-bind="{value}"')
            else:
                attrs.append(f'{key.replace("_", "-")}="{value}"')
        
        attrs_str = ' ' + ' '.join(attrs) if attrs else ''
        
        # Self-closing tags
        if self.tag in ['br', 'hr', 'img', 'input', 'meta', 'link']:
            return f'<{self.tag}{attrs_str} />'
        
        # Build children HTML
        children_html = ''.join(
            child.to_html() if isinstance(child, Element) else str(child) 
            for child in self.children
        )
        
        return f'<{self.tag}{attrs_str}>{children_html}</{self.tag}>'


class HTMLElement:
    """HTML element builder"""
    
    def __init__(self, tag: str):
        self.tag = tag
    
    def __call__(self, *args, **kwargs) -> Element:
        """Create an element with this tag"""
        # First argument can be props dict, or content
        props = {}
        children = []
        
        # Process arguments
        for i, arg in enumerate(args):
            if i == 0 and isinstance(arg, dict):
                # First argument is props
                props = arg
            elif isinstance(arg, Element):
                children.append(arg)
            elif isinstance(arg, list):
                children.extend(arg)
            elif arg is not None:
                children.append(str(arg))
        
        # Add kwargs as props
        props.update(kwargs)
        
        return Element(tag=self.tag, props=props, children=children)


class HTMLBuilder:
    """Builder for HTML elements"""
    
    def __getattr__(self, tag: str) -> HTMLElement:
        """Get HTML element by tag name"""
        return HTMLElement(tag)
    
    def create_element(self, tag: str, props: Dict[str, Any] = None, children: List[Any] = None) -> Element:
        """Create an element with tag, props, and children"""
        if props is None:
            props = {}
        if children is None:
            children = []
        
        return Element(tag=tag, props=props, children=children)


# Global HTML builder instance
html = HTMLBuilder()

# Global event handler registry
_event_handlers: Dict[str, Callable] = {}
_handler_counter = 0


def register_event_handler(handler: Callable) -> str:
    """Register an event handler and return its ID"""
    global _handler_counter
    handler_id = f"handler_{_handler_counter}"
    _handler_counter += 1
    _event_handlers[handler_id] = handler
    return handler_id


def bind(setter_func) -> str:
    """Helper function to get the state key for data binding"""
    if hasattr(setter_func, 'state_key'):
        return setter_func.state_key
    raise ValueError("Function is not a state setter from use_state or use_named_state")


def set_state(setter_func, value_expression: str) -> str:
    """Helper function to generate setState JavaScript for a setter function"""
    if hasattr(setter_func, 'state_key'):
        state_key = setter_func.state_key
        return f"setState('{state_key}', {value_expression})"
    raise ValueError("Function is not a state setter from use_state or use_named_state")


def create_event_handler(setter_func, func_or_value):
    """Create an event handler that mimics ReactPy's lambda syntax"""
    state_key = setter_func.state_key
    
    if callable(func_or_value):
        # If it's a function, we need to apply it to the current state
        func_name = getattr(func_or_value, '__name__', 'anonymous')
        
        # Handle common function patterns
        if func_name == 'increment' or (hasattr(func_or_value, '__code__') and 
                                       'return last_count + 1' in str(func_or_value.__code__.co_consts)):
            return f"setState('{state_key}', (state.{state_key} || 0) + 1)"
        elif func_name == 'decrement' or (hasattr(func_or_value, '__code__') and 
                                         'return last_count - 1' in str(func_or_value.__code__.co_consts)):
            return f"setState('{state_key}', (state.{state_key} || 0) - 1)"
        elif func_name == 'reset_to_zero' or (hasattr(func_or_value, '__code__') and 
                                             'return 0' in str(func_or_value.__code__.co_consts)):
            return f"setState('{state_key}', 0)"
        else:
            # For lambda functions, try to generate appropriate JavaScript
            try:
                # Test the function with a sample value to understand its behavior
                test_result = func_or_value(1)
                if test_result == 2:  # Likely x + 1
                    return f"setState('{state_key}', (state.{state_key} || 0) + 1)"
                elif test_result == 0:  # Likely x - 1
                    return f"setState('{state_key}', (state.{state_key} || 0) - 1)"
                elif test_result == 2:  # Likely x * 2
                    return f"setState('{state_key}', (state.{state_key} || 0) * 2)"
                else:
                    # Generic function call
                    return f"setState('{state_key}', ({func_or_value})(state.{state_key} || 0))"
            except:
                # Fallback to generic handling
                return f"setState('{state_key}', (state.{state_key} || 0))"
    else:
        # Direct value
        return f"setState('{state_key}', {func_or_value})"


class Component:
    """Base class for components"""
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.hook_context = HookContext()
        self._current_state = {}
    
    def render(self) -> Element:
        """Render the component - must be implemented by subclasses"""
        raise NotImplementedError("Component must implement render method")
    
    def mount(self, app: 'QuickTemplate') -> None:
        """Mount component to app"""
        self.app = app
        self.hook_context.component_id = self.id
    
    async def update(self) -> None:
        """Trigger a re-render of the component"""
        if hasattr(self, 'app'):
            await self.app.update_component(self.id)


def component(func: Callable) -> type:
    """Decorator to create a component from a function"""
    class FunctionComponent(Component):
        def __init__(self, *args, **kwargs):
            super().__init__()
            self.args = args
            self.kwargs = kwargs
            self.func = func
        
        def render(self) -> Element:
            # Reset hook context for new render
            self.hook_context.reset()
            
            # Set the hook context for this component
            from .hooks import set_hook_context
            set_hook_context(self.hook_context)
            
            try:
                result = self.func(*self.args, **self.kwargs)
                return result
            finally:
                # Clear hook context
                from .hooks import clear_hook_context
                clear_hook_context()
    
    return FunctionComponent


class QuickTemplate:
    """Template engine for managing components and state"""
    
    def __init__(self, app=None):
        self.app = app
        self.components: Dict[str, Component] = {}
        self.root_component: Optional[Component] = None
        self.rpc_handlers: Dict[str, Callable] = {}
        self.event_handlers: Dict[str, Callable] = {}  # Store lambda functions
        self._setup_rpc_handlers()
    
    def _setup_rpc_handlers(self):
        """Setup default RPC handlers"""
        self.rpc_handlers.update({
            "update_state": self._handle_update_state,
            "dispatch_action": self._handle_dispatch_action,
            "get_initial_state": self._handle_get_initial_state,
            "execute_handler": self._handle_execute_handler,
        })
    
    def register_component(self, component: Component) -> str:
        """Register a component"""
        self.components[component.id] = component
        component.mount(self)
        return component.id
    
    def set_root_component(self, component: Component) -> None:
        """Set the root component"""
        self.root_component = component
        self.register_component(component)
    
    async def update_component(self, component_id: str) -> None:
        """Update a component and notify clients"""
        if component_id in self.components:
            component = self.components[component_id]
            # Re-render component
            new_element = component.render()
            
            # Send update to connected clients
            if hasattr(self, '_websocket_manager'):
                await self._websocket_manager.broadcast({
                    "type": "component_update",
                    "componentId": component_id,
                    "element": new_element.to_dict()
                })
    
    async def _handle_update_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle state update RPC call"""
        component_id = data.get("componentId")
        state_key = data.get("stateKey")
        value = data.get("value")
        
        if component_id in self.components:
            component = self.components[component_id]
            if hasattr(component.hook_context, 'states') and state_key in component.hook_context.states:
                component.hook_context.states[state_key] = value
                await self.update_component(component_id)
                return {"success": True}
        
        return {"success": False, "error": "Component or state not found"}
    
    async def _handle_dispatch_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle action dispatch RPC call"""
        component_id = data.get("componentId")
        action = data.get("action")
        
        if component_id in self.components:
            component = self.components[component_id]
            if hasattr(component.hook_context, 'reducers'):
                for reducer_info in component.hook_context.reducers.values():
                    reducer_func = reducer_info['reducer']
                    state_key = reducer_info['state_key']
                    current_state = component.hook_context.states.get(state_key)
                    
                    try:
                        new_state = reducer_func(current_state, action)
                        component.hook_context.states[state_key] = new_state
                        await self.update_component(component_id)
                        return {"success": True}
                    except Exception as e:
                        return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Component or reducer not found"}
    
    async def _handle_get_initial_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get initial state RPC call"""
        component_id = data.get("componentId")
        
        if component_id in self.components:
            component = self.components[component_id]
            if hasattr(component.hook_context, 'states'):
                return {"success": True, "state": component.hook_context.states}
        
        return {"success": False, "error": "Component not found"}
    
    async def _handle_execute_handler(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle lambda function execution"""
        handler_id = data.get("handlerId")
        component_id = data.get("componentId")
        
        if handler_id in _event_handlers and component_id in self.components:
            component = self.components[component_id]
            handler = _event_handlers[handler_id]
            
            try:
                # Create a mock event object
                class MockEvent:
                    def __init__(self):
                        self.target = None
                        self.preventDefault = lambda: None
                
                # Execute the handler with mock event
                result = handler(MockEvent())
                
                # If the result is a function (like increment/decrement), 
                # we need to find which state setter to call
                if callable(result):
                    # This is a function that should be passed to a setter
                    # We'll need to track which setter this is for
                    # For now, let's assume it's for the first state
                    if component.hook_context.states:
                        first_state_key = list(component.hook_context.states.keys())[0]
                        current_value = component.hook_context.states[first_state_key]
                        new_value = result(current_value)
                        component.hook_context.states[first_state_key] = new_value
                        await self.update_component(component_id)
                
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Handler or component not found"}
    
    def render_to_dict(self) -> Dict[str, Any]:
        """Render the root component to dictionary"""
        if self.root_component:
            return self.root_component.render().to_dict()
        return {"tag": "div", "props": {}, "children": [], "key": None, "componentId": None}


def run(component_func: Callable, host: str = "127.0.0.1", port: int = 8000, debug: bool = False):
    """Run a component as a web application"""
    from ..app import QuickAPI
    from .response import TemplateResponse
    
    app = QuickAPI(debug=debug)
    template_engine = QuickTemplate(app)
    
    # Create and register the root component
    if isinstance(component_func, type):
        # If it's a class (from @component decorator), instantiate it
        root_component = component_func()
    else:
        # If it's a function, call it directly
        root_component = component_func
    template_engine.set_root_component(root_component)
    
    # Setup template routes
    @app.get("/")
    async def index(request):
        return TemplateResponse(template_engine)
    
    # Setup RPC endpoint
    @app.post("/rpc")
    async def rpc_handler(request):
        data = await request.json()
        method = data.get("method")
        params = data.get("params", {})
        
        if method in template_engine.rpc_handlers:
            result = await template_engine.rpc_handlers[method](params)
            return {"result": result}
        else:
            return {"error": f"Unknown method: {method}"}
    
    # Setup WebSocket for real-time updates
    @app.websocket("/ws")
    async def websocket_handler(websocket):
        template_engine._websocket_manager = websocket
        try:
            await websocket.accept()
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                # Handle RPC calls via WebSocket
                method = data.get("method")
                params = data.get("params", {})
                
                if method in template_engine.rpc_handlers:
                    result = await template_engine.rpc_handlers[method](params)
                    await websocket.send_text(json.dumps({
                        "id": data.get("id"),
                        "result": result
                    }))
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
    
    # Run the app
    import uvicorn
    uvicorn.run(app, host=host, port=port)