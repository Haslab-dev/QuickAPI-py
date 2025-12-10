# QuickAPI - Modern Python Framework for AI-Native APIs & UIs

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.0.1-red.svg)](https://github.com/quickapi/quickapi)

**QuickAPI** is a modern Python web framework designed for building AI-native APIs and interactive UIs. It combines the power of FastAPI-style APIs with Gradio-like UI components, plus native support for LLMs, RAG systems, embeddings, and templates.

## 🎯 Why QuickAPI?

- **🚀 Fast** - Up to 2.92x faster than FastAPI in real-world scenarios
- **🤖 AI-Native** - Built-in LLM, RAG, and embeddings support
- **🎨 UI Components** - Gradio-like interface components for rapid prototyping
- **📄 Template Engine** - File-based HTML templates with Python f-string syntax
- **🔌 Pluggable** - Modular architecture with swappable backends
- **💾 Database-Ready** - Abstract storage layers for easy SQLite/PostgreSQL integration
- **📦 Lightweight** - Install only what you need
- **🎨 Simple** - Less boilerplate, more productivity

## �  Performance Benchmarks

QuickAPI consistently outperforms popular Python frameworks:

```
Framework Comparison (5000 requests, 50 concurrent)
┌───────────┬──────────┬──────────────────┬──────────────┐
│ Framework │ RPS      │ Avg Latency (ms) │ Success Rate │
├───────────┼──────────┼──────────────────┼──────────────┤
│ QuickAPI  │ 2,226    │ 0.45             │ 100.0%       │
│ FastAPI   │   762    │ 1.31             │ 100.0%       │
│ Flask     │ 2,040    │ 0.49             │ 100.0%       │
└───────────┴──────────┴──────────────────┴──────────────┘

🥇 QuickAPI is 2.92x faster than FastAPI
🥈 QuickAPI is 1.09x faster than Flask
```

*Benchmarks run on macOS with Python 3.13. See [benchmarks/](benchmarks/) for details.*

## 📦 Installation

```bash
# Core framework only
pip install quickapi

# With AI support (LLM, RAG, Embeddings)
pip install quickapi[ai]

# With all features
pip install quickapi[all]
```

## 🏁 Quick Start

### 1. Minimal API (Hello World)

```python
from quickapi import QuickAPI, JSONResponse

app = QuickAPI(title="My API", version="1.0.0")

@app.get("/")
async def root(request):
    return JSONResponse({"message": "Hello from QuickAPI!"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. Interactive UI Component

```python
from quickapi import QuickAPI
from quickapi.ui import UI, Textbox, Text
from quickapi.templates import default_layout, TemplateResponse

def analyze_sentiment(text):
    """Simple sentiment analysis"""
    positive_words = ["good", "great", "awesome", "love", "happy"]
    negative_words = ["bad", "terrible", "hate", "sad", "awful"]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return "😊 Positive"
    elif negative_count > positive_count:
        return "😢 Negative"
    else:
        return "😐 Neutral"

app = QuickAPI(title="Sentiment Analysis")

# Create UI interface
sentiment_ui = UI(
    fn=analyze_sentiment,
    inputs=Textbox(label="Enter text", placeholder="Type something here..."),
    outputs=Text(label="Sentiment"),
    title="📝 Sentiment Analysis",
    description="Analyze the sentiment of text."
)

@app.get("/")
async def sentiment_page(request):
    """Serve the sentiment analysis UI"""
    layout = default_layout(sentiment_ui.title)
    template = sentiment_ui._render_template()
    return TemplateResponse(
        template_string=layout.wrap(template),
        title=sentiment_ui.title,
        custom_js=sentiment_ui._get_javascript()
    )

# Setup API endpoint for the UI
sentiment_ui._setup_api_endpoint(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. AI Chatbot with Conversation History

```python
import os
from quickapi import QuickAPI, JSONResponse
from quickapi.ai import LLM, ConversationManager

# Initialize LLM (supports OpenAI, Claude, or custom providers)
llm = LLM(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Conversation manager with pluggable storage (in-memory, SQLite, PostgreSQL)
conversation_manager = ConversationManager()

app = QuickAPI(title="AI Chatbot")

@app.post("/chat/{conversation_id}")
async def chat(request, conversation_id: str):
    body = await request.json()
    message = body.get("message", "")
    
    # Get or create conversation
    conversation = conversation_manager.get_or_create_conversation(conversation_id)
    
    # Add user message
    conversation.add_message("user", message)
    
    # Build context with system prompt + history
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."}
    ]
    messages.extend(conversation.get_context())
    
    # Get AI response
    result = await llm.chat(messages, temperature=0.7)
    
    # Save assistant response
    conversation.add_message("assistant", result["content"])
    
    return JSONResponse({
        "response": result["content"],
        "conversation_id": conversation_id
    })
```

### 4. RAG (Retrieval-Augmented Generation) System

```python
import os
from quickapi import QuickAPI, JSONResponse
from quickapi.ai import LLM, RAG, Embeddings, ConversationManager
from quickapi.ai.vectors import InMemoryVectorStore

# Initialize components
llm = LLM("openai", api_key=os.getenv("OPENAI_API_KEY"))
embeddings = Embeddings("openai", api_key=os.getenv("OPENAI_API_KEY"))
vector_store = InMemoryVectorStore(dimension=embeddings.get_dimension())

# Initialize RAG system
rag = RAG(
    embeddings=embeddings,
    llm=llm,
    vector_store=vector_store,
    similarity_threshold=0.3  # Adjust for precision/recall tradeoff
)

conversation_manager = ConversationManager()

app = QuickAPI(title="RAG Knowledge Base")

@app.post("/documents")
async def upload_document(request):
    """Upload documents to knowledge base"""
    body = await request.json()
    text = body.get("text", "")
    
    # Add document (automatically chunks, embeds, and stores)
    doc_ids = await rag.add_texts([text])
    
    return JSONResponse({"id": doc_ids[0], "status": "uploaded"})

@app.post("/chat/{conversation_id}")
async def rag_chat(request, conversation_id: str):
    """Chat with your documents"""
    body = await request.json()
    message = body.get("message", "")
    
    conversation = conversation_manager.get_or_create_conversation(conversation_id)
    conversation.add_message("user", message)
    
    # RAG answer with retrieved context
    result = await rag.answer(message, top_k=3)
    
    conversation.add_message("assistant", result["answer"])
    
    return JSONResponse({
        "answer": result["answer"],
        "sources": result["sources"],  # Retrieved documents with scores
        "conversation_id": conversation_id
    })
```

## 🎨 UI Components & Templates

### Interactive UI Components

Build Gradio-like interfaces with minimal code:

```python
from quickapi import QuickAPI
from quickapi.ui import UI, Textbox, Number, Text

def calculate_power(base, exponent):
    """Calculate base to the power of exponent"""
    try:
        result = base ** exponent
        return f"{base}^{exponent} = {result}"
    except Exception as e:
        return f"Error: {str(e)}"

app = QuickAPI(title="Power Calculator")

# Create UI interface
power_ui = UI(
    fn=calculate_power,
    inputs=[
        Number(label="Base", value=2),
        Number(label="Exponent", value=3)
    ],
    outputs=Text(label="Result"),
    title="🔢 Power Calculator",
    description="Calculate base to the power of exponent."
)

@app.get("/calculator")
async def calculator_page(request):
    """Serve the calculator UI"""
    layout = default_layout(power_ui.title)
    template = power_ui._render_template()
    return TemplateResponse(
        template_string=layout.wrap(template),
        title=power_ui.title,
        custom_js=power_ui._get_javascript()
    )

# Setup API endpoint for the UI
power_ui._setup_api_endpoint(app)
```

### Available Components

```python
from quickapi.ui import (
    UI,           # Main UI container
    Textbox,      # Text input/textarea
    Number,       # Number input
    Slider,       # Range slider
    Button,       # Action button
    Text          # Text output display
)

# Text input
text_input = Textbox(
    label="Enter text",
    placeholder="Type here...",
    lines=3  # Multi-line textarea
)

# Number input
number_input = Number(
    label="Amount",
    value=100,
    minimum=0,
    maximum=1000,
    step=10
)

# Slider
slider_input = Slider(
    label="Temperature",
    value=0.7,
    minimum=0.0,
    maximum=1.0,
    step=0.1
)

# Button
submit_btn = Button(
    value="Submit",
    variant="primary",  # primary, secondary, success, danger
    size="medium"       # small, medium, large
)

# Text output
text_output = Text(
    label="Result",
    value="Output will appear here..."
)
```

### Template Engine

File-based HTML templates with Python f-string syntax:

```python
from quickapi import QuickAPI
from quickapi.templates import Template, TemplateResponse, default_layout

app = QuickAPI()
template_engine = Template(app)

# Create template file: templates/demo.html
"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto p-8">
        <h1 class="text-3xl font-bold mb-4">{title}</h1>
        <p class="text-lg mb-4">{message}</p>
        <ul class="list-disc list-inside">
            <li>{item1}</li>
            <li>{item2}</li>
            <li>{item3}</li>
        </ul>
    </div>
</body>
</html>
"""

@template_engine.route("/demo", "templates/demo.html")
async def demo_page(request):
    """Template with context data"""
    return {
        "title": "QuickAPI Demo",
        "message": "Hello from the template engine!",
        "item1": "Fast rendering",
        "item2": "Simple syntax",
        "item3": "Tailwind CSS support"
    }
```

### Layout System

Pre-built layouts with theme support:

```python
from quickapi.templates import Layout, default_layout, dark_layout, minimal_layout

# Default layout
layout = default_layout("My App")
html = layout.wrap("<h1>Content</h1>")

# Dark theme
dark = dark_layout("My App")

# Minimal layout
minimal = minimal_layout("My App")

# Custom layout
custom_layout = Layout(
    title="Custom App",
    theme="dark",
    custom_css="body { font-family: 'Comic Sans MS'; }",
    custom_js="console.log('Custom JS loaded');"
)
```

## 🤖 AI Features

### LLM Support

Unified interface for multiple LLM providers:

```python
from quickapi.ai import LLM

# OpenAI
llm = LLM("openai", api_key="sk-...")

# Claude
llm = LLM("claude", api_key="sk-ant-...")

# OpenAI-compatible (Vercel AI Gateway, Groq, etc.)
llm = LLM("openai", api_key="...", base_url="https://api.groq.com/v1")

# Chat completion
response = await llm.chat([
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello!"}
], model="gpt-4", temperature=0.7)

print(response["content"])

# Streaming
async for token in llm.stream([
    {"role": "user", "content": "Tell me a story"}
]):
    print(token, end="", flush=True)
```

### RAG (Retrieval-Augmented Generation)

Built-in RAG with automatic chunking, embedding, and retrieval:

```python
from quickapi.ai import RAG, Embeddings, LLM

# Initialize RAG
rag = RAG(
    embeddings=Embeddings("openai", api_key="..."),
    llm=LLM("openai", api_key="..."),
    top_k=5,
    similarity_threshold=0.3
)

# Add documents (automatically chunks and embeds)
await rag.add_texts([
    "QuickAPI is a modern Python framework for AI-native APIs.",
    "It provides built-in support for LLM, RAG, and embeddings."
])

# Query with automatic context retrieval
result = await rag.answer("What is QuickAPI?")

print(result["answer"])  # AI-generated answer
print(result["sources"])  # Retrieved documents with similarity scores
```

### Embeddings & Vector Search

```python
from quickapi.ai import Embeddings

# Initialize embeddings
embeddings = Embeddings("openai", api_key="...", model="text-embedding-3-small")

# Generate embeddings
embedding = await embeddings.embed("Hello, world!")
print(embedding.shape)  # (1536,)

# Batch embeddings
embeddings_batch = await embeddings.embed([
    "First document",
    "Second document"
])

# Semantic search
results = await embeddings.search(
    query="machine learning",
    documents=["AI is transforming tech", "Python is popular"],
    top_k=2
)
```

### Conversation Management

Database-ready conversation storage with pluggable backends:

```python
from quickapi.ai import ConversationManager, ChatMemory

# In-memory (default)
manager = ConversationManager()

# SQLite (future)
# from quickapi.ai.chat_memory import SQLiteChatBackend
# backend = SQLiteChatBackend("chat.db")
# manager = ConversationManager(backend=backend)

# Create conversation
conv_id = manager.create_conversation()

# Get conversation
conversation = manager.get_conversation(conv_id)

# Add messages
conversation.add_message("user", "Hello!")
conversation.add_message("assistant", "Hi there!")

# Get context for LLM
context = conversation.get_context()  # Returns last N messages

# Export/import
data = conversation.export_conversation(format="json")
conversation.load_conversation(data, format="json")
```

### Vector Stores

Pluggable vector storage backends:

```python
from quickapi.ai.vectors import InMemoryVectorStore

# In-memory vector store
vector_store = InMemoryVectorStore(dimension=1536)

# Add vectors
await vector_store.add_vectors(
    vectors=embeddings_array,
    ids=["doc1", "doc2"],
    metadata=[{"source": "file1"}, {"source": "file2"}]
)

# Search
results = await vector_store.search(
    query_vector=query_embedding,
    top_k=5
)

# Future: FAISS, Qdrant, Pinecone, etc.
```

## 🌐 WebSocket & Streaming

### WebSocket Support

```python
from quickapi import QuickAPI
from quickapi.websocket import WebSocket

app = QuickAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"Echo: {message}")
    except:
        await websocket.close()
```

### Server-Sent Events (SSE)

```python
from quickapi import QuickAPI
from quickapi.response import ServerSentEventResponse

app = QuickAPI()

@app.get("/events")
async def events(request):
    async def generate_events():
        for i in range(10):
            yield {"data": f"Event {i}", "event": "update"}
    
    return ServerSentEventResponse(generate_events())
```

## 🔧 Middleware

### CORS

```python
from quickapi.middleware import CORSMiddleware

app.middleware(CORSMiddleware(
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True
))
```

### JWT Authentication

```python
from quickapi.middleware import JWTAuthMiddleware

app.middleware(JWTAuthMiddleware(
    secret_key="your-secret-key",
    algorithm="HS256",
    exclude_paths=["/health", "/docs", "/auth/login"]
))
```

### Custom Middleware

```python
from quickapi.middleware import BaseMiddleware

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, request, call_next):
        print(f"Request: {request.method} {request.path}")
        response = await call_next(request)
        print(f"Response: {response.status_code}")
        return response

app.middleware(LoggingMiddleware())
```

## 📚 Examples

Check out the [examples/](examples/) directory for complete working examples:

### API Examples
- **[minimal_api.py](examples/minimal_api.py)** - Basic REST API
- **[simple_chatbot.py](examples/simple_chatbot.py)** - AI chatbot with conversation history
- **[simple_rag.py](examples/simple_rag.py)** - RAG system with document upload and Q&A
- **[full_api.py](examples/full_api.py)** - Complete REST API with auth, CRUD, and docs

### UI & Template Examples
- **[simple_demo.py](examples/simple_demo.py)** - Complete demo with templates and UI components
  - Template engine with HTML files
  - Interactive sentiment analysis UI
  - Power calculator with number inputs
  - Responsive design with Tailwind CSS

Run any example:
```bash
python examples/simple_demo.py
# Open http://localhost:8000

# Available routes:
# GET  /                    - Main demo page
# GET  /template            - Simple template demo
# GET  /template/advanced   - Advanced template demo  
# GET  /sentiment           - Sentiment analysis UI
# GET  /power              - Power calculator UI
```

## 🔗 API Documentation

QuickAPI automatically generates OpenAPI/Swagger documentation:

- **Interactive docs**: `http://localhost:8000/docs`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

Add documentation to your endpoints:

```python
from quickapi import api_doc

@app.get("/users/{user_id}")
@api_doc(
    summary="Get user by ID",
    tags=["Users"],
    responses={
        "200": {"description": "User found"},
        "404": {"description": "User not found"}
    }
)
async def get_user(request, user_id: str):
    return JSONResponse({"id": user_id, "name": "John"})
```

## 🧩 Architecture

```
QuickAPI
├── Core Framework
│   ├── ASGI Server (Uvicorn)
│   ├── Router & Request Handling
│   ├── Response Types (JSON, HTML, SSE, Stream)
│   ├── WebSocket Support
│   └── OpenAPI/Swagger Generation
│
├── Template Engine (quickapi.templates)
│   ├── Template
│   │   ├── File-based Templates
│   │   ├── Python f-string Syntax
│   │   └── Route Integration
│   │
│   ├── Layout System
│   │   ├── Default Layout
│   │   ├── Dark Theme
│   │   ├── Minimal Theme
│   │   └── Custom Layouts
│   │
│   └── Response Types
│       ├── TemplateResponse
│       └── TemplateJSONResponse
│
├── UI Components (quickapi.ui)
│   ├── UI Container
│   │   ├── Function Wrapping
│   │   ├── Auto API Generation
│   │   └── JavaScript Integration
│   │
│   └── Components
│       ├── Textbox (input/textarea)
│       ├── Number (numeric input)
│       ├── Slider (range input)
│       ├── Button (actions)
│       └── Text (output display)
│
├── Middleware Layer
│   ├── CORS
│   ├── JWT Authentication
│   ├── Rate Limiting
│   └── Custom Middleware
│
├── AI Module (quickapi.ai)
│   ├── LLM
│   │   ├── OpenAI Provider
│   │   ├── Claude Provider
│   │   └── Custom Provider
│   │
│   ├── Embeddings
│   │   ├── OpenAI Embeddings
│   │   ├── Sentence Transformers
│   │   └── Custom Embeddings
│   │
│   ├── RAG
│   │   ├── Document Management
│   │   ├── Text Splitting
│   │   ├── Retrieval
│   │   └── Answer Generation
│   │
│   ├── Chat Memory
│   │   ├── In-Memory Backend
│   │   ├── SQLite Backend (future)
│   │   └── PostgreSQL Backend (future)
│   │
│   └── Vector Stores
│       ├── InMemoryVectorStore
│       ├── FAISS (future)
│       └── Qdrant (future)
│
└── CLI Tools
    ├── Project Scaffolding
    ├── Development Server
    └── Docker Generation
```

## 🛣 Roadmap

### ✅ v0.0.1 (Current - MVP)
- [x] Core ASGI framework
- [x] JSON/HTML responses
- [x] WebSocket support
- [x] Template engine with file-based templates
- [x] UI components (Textbox, Number, Slider, Button, Text)
- [x] Layout system with themes
- [x] LLM integration (OpenAI, Claude)
- [x] RAG with vector search
- [x] Embeddings
- [x] Conversation management
- [x] In-memory vector store
- [x] OpenAPI/Swagger docs
- [x] Middleware (CORS, JWT)

### 🚧 v0.0.5 (Next)
- [ ] CLI tool (`quickapi create`, `quickapi run`)
- [ ] SQLite chat backend
- [ ] PostgreSQL chat backend
- [ ] FAISS vector store
- [ ] Streaming RAG responses
- [ ] Model auto-loader
- [ ] Enhanced benchmarks

### 🔮 v0.1.0 (Public Beta)
- [ ] Qdrant vector store
- [ ] Redis chat backend
- [ ] Plugin system
- [ ] Web playground UI
- [ ] Production deployment guides
- [ ] Performance optimizations

### 🎯 v1.0 (Stable)
- [ ] Production-ready
- [ ] Comprehensive documentation
- [ ] Community plugins
- [ ] Enterprise features
- [ ] Multi-language support

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Report bugs** - Open an issue with details
2. **Suggest features** - Share your ideas
3. **Submit PRs** - Fix bugs or add features
4. **Write docs** - Improve documentation
5. **Share examples** - Show what you've built

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

QuickAPI is licensed under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Inspired by **FastAPI**'s elegant API design
- Built on **Starlette** and **Uvicorn** for ASGI support
- AI patterns influenced by **LangChain** and **LlamaIndex**
- Performance insights from the Python async community

## 📞 Support

- **Documentation**: [Coming soon]
- **Issues**: [GitHub Issues](https://github.com/quickapi/quickapi/issues)
- **Discussions**: [GitHub Discussions](https://github.com/quickapi/quickapi/discussions)

---

**Built with ❤️ for the AI developer community**
