"""
QuickAPI - Modern Python web framework for AI-native APIs

The fastest Python API framework with first-class AI support.
"""

__version__ = "0.0.1"
__author__ = "QuickAPI Team"
__email__ = "team@quickapi.dev"

from .app import QuickAPI
from .router import Route
from .response import JSONResponse, StreamingResponse
from .middleware import Middleware, CORSMiddleware
from .websocket import WebSocket, WebSocketDisconnect
from .openapi import api_doc, request_body, response, requires_auth

# Template engine imports
from .templates import (
    Component, html, run, bind, set_state, create_event_handler, use_state, use_reducer, use_named_state, TemplateResponse,
    BaseLayout, DefaultLayout, MinimalLayout, LayoutConfig,
    create_bootstrap_layout, create_tailwind_layout, create_custom_layout
)

__all__ = [
    "QuickAPI",
    "Route",
    "JSONResponse",
    "StreamingResponse",
    "Middleware",
    "CORSMiddleware",
    "WebSocket",
    "WebSocketDisconnect",
    "api_doc",
    "request_body",
    "response",
    "requires_auth",
    # Template engine exports
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
    "create_custom_layout",
]

# AI modules - lazy import to avoid heavy dependencies
def _lazy_import_ai():
    try:
        from .ai.llm import LLM
        from .ai.rag import RAG
        from .ai.embeddings import Embeddings
        from .ai.chat_memory import ChatMemory, ConversationManager
        return {
            "LLM": LLM,
            "RAG": RAG,
            "Embeddings": Embeddings,
            "ChatMemory": ChatMemory,
            "ConversationManager": ConversationManager
        }
    except ImportError:
        return {}

# Make AI modules available when dependencies are installed
_ai_modules = _lazy_import_ai()
for name, module in _ai_modules.items():
    globals()[name] = module
    __all__.append(name)