"""
QuickAPI Templating Engine

A ReactPy-like templating system with state management and RPC reactivity.
"""

from .core import Component, html, run, bind, set_state, create_event_handler
from .hooks import use_state, use_reducer, use_named_state
from .response import TemplateResponse
from .layout import (
    BaseLayout, 
    DefaultLayout, 
    MinimalLayout, 
    LayoutConfig,
    create_bootstrap_layout,
    create_tailwind_layout,
    create_custom_layout
)

__all__ = [
    "Component",
    "html", 
    "run",
    "bind",
    "set_state",
    "create_event_handler",
    "use_state",
    "use_reducer",
    "use_named_state",
    "TemplateResponse",
    "BaseLayout",
    "DefaultLayout", 
    "MinimalLayout",
    "LayoutConfig",
    "create_bootstrap_layout",
    "create_tailwind_layout",
    "create_custom_layout"
]