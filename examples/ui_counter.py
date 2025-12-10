"""
Counter - exactly like  syntax
"""

import quickapi
from quickapi.templates.core import component
from quickapi.templates.hooks import use_state
from quickapi import create_event_handler


def increment(last_count):
    return last_count + 1


def decrement(last_count):
    return last_count - 1


@component
def Counter():
    initial_count = 0
    count, set_count = use_state(initial_count)
    
    return quickapi.html.div(
        {"class": "min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 flex items-center justify-center p-8"},
        quickapi.html.div(
            {"class": "bg-white rounded-3xl shadow-2xl p-10 max-w-lg w-full border border-purple-100"},
            quickapi.html.div(
                {"class": "text-center mb-8"},
                quickapi.html.h1(
                    {"class": "text-4xl font-bold text-purple-800 mb-2"},
                    "Perfect  Style"
                ),
                quickapi.html.p(
                    {"class": "text-purple-600"},
                    "Identical syntax to "
                )
            ),
            
            quickapi.html.div(
                {"class": "text-center mb-10"},
                quickapi.html.div(
                    {"class": "text-8xl font-bold text-purple-600 mb-4"},
                    f"Count: ",
                    quickapi.html.span({"data_bind": set_count.state_key}, str(count))
                )
            ),
            
            # -style event handlers
            quickapi.html.div(
                {"class": "flex gap-4 justify-center mb-8"},
                quickapi.html.button(
                    {
                        "class": "px-8 py-4 bg-red-500 hover:bg-red-600 text-white rounded-xl font-bold text-lg transition-all duration-200 hover:scale-105 shadow-lg",
                        "on_click": create_event_handler(set_count, initial_count)  # : lambda event: set_count(initial_count)
                    },
                    "Reset"
                ),
                quickapi.html.button(
                    {
                        "class": "px-8 py-4 bg-gray-500 hover:bg-gray-600 text-white rounded-xl font-bold text-lg transition-all duration-200 hover:scale-105 shadow-lg",
                        "on_click": create_event_handler(set_count, decrement)  # : lambda event: set_count(decrement)
                    },
                    "−"
                ),
                quickapi.html.button(
                    {
                        "class": "px-8 py-4 bg-purple-500 hover:bg-purple-600 text-white rounded-xl font-bold text-lg transition-all duration-200 hover:scale-105 shadow-lg",
                        "on_click": create_event_handler(set_count, increment)  # : lambda event: set_count(increment)
                    },
                    "+"
                )
            ),
            
            # More -style examples
            quickapi.html.div(
                {"class": "space-y-4"},
                quickapi.html.button(
                    {
                        "class": "w-full px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors",
                        "on_click": create_event_handler(set_count, lambda x: x * 2)  # : lambda event: set_count(lambda x: x * 2)
                    },
                    "Double (λx: x * 2)"
                ),
                quickapi.html.button(
                    {
                        "class": "w-full px-6 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors",
                        "on_click": create_event_handler(set_count, lambda x: max(0, x - 5))  # : lambda event: set_count(lambda x: max(0, x - 5))
                    },
                    "Subtract 5 (λx: max(0, x - 5))"
                ),
                quickapi.html.button(
                    {
                        "class": "w-full px-6 py-3 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg font-medium transition-colors",
                        "on_click": create_event_handler(set_count, 42)  # : lambda event: set_count(42)
                    },
                    "Set to 42"
                )
            ),
            
            # Code comparison
            quickapi.html.div(
                {"class": "mt-10 p-6 bg-gray-50 rounded-xl"},
                quickapi.html.h3(
                    {"class": "font-bold text-gray-800 mb-4 text-lg"},
                    "🔥  Syntax Comparison:"
                ),
                quickapi.html.div(
                    {"class": "space-y-3 text-sm font-mono"},
                    quickapi.html.div(
                        {"class": "p-3 bg-purple-100 rounded-lg"},
                        quickapi.html.div({"class": "font-bold text-purple-800"}, ":"),
                        quickapi.html.div({"class": "text-purple-700"}, 'lambda event: set_count(increment)')
                    ),
                    quickapi.html.div(
                        {"class": "p-3 bg-blue-100 rounded-lg"},
                        quickapi.html.div({"class": "font-bold text-blue-800"}, "QuickAPI:"),
                        quickapi.html.div({"class": "text-blue-700"}, 'create_event_handler(set_count, increment)')
                    )
                ),
                quickapi.html.p(
                    {"class": "text-gray-600 mt-4 text-sm"},
                    "✨ Same functionality, clean syntax, reactive updates!"
                )
            )
        )
    )


def create_app():
    """Create the QuickAPI app"""
    from quickapi.app import QuickAPI
    from quickapi.templates.response import TemplateResponse
    from quickapi.templates.core import QuickTemplate
    from quickapi import create_tailwind_layout
    
    app = QuickAPI(debug=True)
    template_engine = QuickTemplate(app)
    
    # Create Tailwind layout
    layout = create_tailwind_layout("Perfect  Style")
    
    # Create and register the root component
    root_component = Counter()
    template_engine.set_root_component(root_component)
    
    @app.get("/")
    async def index(request):
        return TemplateResponse(template_engine, layout=layout)
    
    return app


if __name__ == "__main__":
    app = create_app()
    print("🚀 Perfect -Style Counter")
    print("🎯  Syntax:")
    print("   def increment(last_count): return last_count + 1")
    print("   count, set_count = use_state(initial_count)")
    print("   on_click: lambda event: set_count(increment)")
    print("")
    print("✨ QuickAPI Equivalent:")
    print("   def increment(last_count): return last_count + 1")
    print("   count, set_count = use_state(initial_count)")
    print("   on_click: create_event_handler(set_count, increment)")
    print("")
    print("🌐 Open: http://127.0.0.1:8000")
    
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)