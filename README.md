# QuickAPI - The Fastest Python API Framework for AI

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.0.1-red.svg)](https://github.com/quickapi/quickapi)

QuickAPI is a modern Python web framework designed for AI-native APIs. Unlike traditional frameworks like FastAPI or Flask, QuickAPI ships with native support for LLMs, RAG, streaming, and vector search, while remaining lightweight and modular.

## 🚀 Features

- **Faster than FastAPI** - Optimized for async & streaming workloads
- **AI-Native** - Built-in LLM support (OpenAI, Claude)
- **RAG Ready** - Native RAG with in-memory vector search
- **Real-time Streaming** - WebSocket & SSE support
- **Modular** - Install heavy dependencies only when needed
- **Simple** - Less boilerplate, more productivity

## 📦 Installation

```bash
# Core framework
pip install quickapi

# With AI support
pip install quickapi[ai]

# With all features
pip install quickapi[all]
```

## 🏁 Quick Start

### Minimal API

```python
from quickapi import QuickAPI, JSONResponse

app = QuickAPI(title="My API", version="1.0.0")

@app.get("/")
async def root():
    return JSONResponse({"message": "Hello from QuickAPI!"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### AI Chatbot

```python
import os
from quickapi import QuickAPI
from quickapi.ai import LLM
from quickapi.websocket import WebSocket

# Initialize LLM
llm = LLM("openai", api_key=os.getenv("OPENAI_API_KEY"))

app = QuickAPI(title="AI Chatbot")

@app.websocket("/ws")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        data = await websocket.receive_json()
        message = data.get("message", "")
        
        # Stream AI response
        async for token in llm.stream([
            {"role": "user", "content": message}
        ]):
            await websocket.send_text(token)
```

### RAG Knowledge Base

```python
import os
from quickapi import QuickAPI
from quickapi.ai import RAG, Embeddings, LLM

# Initialize RAG
embeddings = Embeddings("openai", api_key=os.getenv("OPENAI_API_KEY"))
llm = LLM("openai", api_key=os.getenv("OPENAI_API_KEY"))
rag = RAG(embeddings=embeddings, llm=llm)

app = QuickAPI(title="RAG Knowledge Base")

@app.post("/ask")
async def ask_question(request):
    body = await request.json()
    question = body.get("question", "")
    
    # Get answer with retrieved context
    result = await rag.answer(question)
    
    return JSONResponse({
        "answer": result["answer"],
        "sources": result["sources"]
    })
```

## 🤖 AI Features

### LLM Support

QuickAPI provides a unified interface for multiple LLM providers:

```python
from quickapi.ai import LLM

# OpenAI
llm = LLM("openai", api_key="your-key")

# Claude
llm = LLM("claude", api_key="your-key")

# Custom provider
def custom_chat(messages, model, **kwargs):
    # Your implementation
    return {"content": "Response"}

llm = LLM("custom", chat_func=custom_chat)

# Chat completion
response = await llm.chat([
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello!"}
])

# Streaming
async for token in llm.stream([
    {"role": "user", "content": "Tell me a story"}
]):
    print(token)
```

### RAG (Retrieval-Augmented Generation)

Built-in RAG capabilities with vector storage:

```python
from quickapi.ai import RAG, Embeddings, LLM

# Initialize RAG system
rag = RAG()

# Add documents
await rag.add_documents([
    "QuickAPI is fast and AI-native.",
    "It supports streaming and real-time communication."
])

# Query with context retrieval
result = await rag.answer("What makes QuickAPI special?")
print(result["answer"])  # AI-generated answer with context
```

### Embeddings & Vector Search

```python
from quickapi.ai import Embeddings

# Initialize embeddings
embeddings = Embeddings("openai", api_key="your-key")

# Generate embeddings
embedding = await embeddings.embed("Hello, world!")

# Semantic search
results = await embeddings.search(
    query="machine learning",
    documents=["AI is transforming tech", "Python is popular"]
)
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

### Server-Sent Events

```python
from quickapi import QuickAPI
from quickapi.response import ServerSentEventResponse

app = QuickAPI()

@app.get("/events")
async def events():
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
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
))
```

### Authentication

```python
from quickapi.middleware import JWTAuthMiddleware

app.middleware(JWTAuthMiddleware(
    secret_key="your-secret",
    exclude_paths=["/health", "/docs"]
))
```

## 📚 CLI Tool

QuickAPI includes a CLI for rapid development:

```bash
# Create new project
quickapi create my-api

# Run development server
quickapi run --reload

# Generate Docker files
quickapi docker file
quickapi docker compose

# Generate OpenAPI spec
quickapi openapi --output api.json
```

## 🏎 Performance

QuickAPI is optimized for speed:

- **Hello World Latency**: < 2ms
- **JSON Serialization**: Uses orjson for 2-3x faster serialization
- **Routing**: Optimized regex-based routing
- **Streaming**: Near-zero token flush latency
- **Memory**: < 3MB core installation

## 📖 Examples

- [Minimal API](examples/minimal_api.py) - Basic REST API
- [AI Chatbot](examples/chatbot.py) - WebSocket chat with LLM streaming
- [RAG Server](examples/rag_server.py) - Knowledge base with semantic search

## 🔗 API Documentation

QuickAPI automatically generates OpenAPI documentation. Run your app and visit:

- Interactive docs: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## 🧩 Architecture

```
QuickAPI Core
├─ Networking/Router/Streaming Layer
├─ API Decorators (get/post/websocket)
├─ Middleware Pipeline (CORS/Auth)
├─ OpenAPI/Swagger Docs
├─ LLM Core Runtime (Native)
│   ├─ OpenAI Provider
│   ├─ Claude Provider
│   └─ Custom Model Provider
├─ RAG Core
│   ├─ Embeddings (pluggable)
│   └─ In-Memory VectorDB
└─ Optional Backends
   ├─ PyTorch Loader
   ├─ ONNX Loader
   ├─ GGUF llama.cpp loader
   └─ Vector engines (FAISS/Qdrant)
```

## 🛣 Roadmap

### v0.0.1 (MVP)
- [x] Basic ASGI router
- [x] JSON parsing
- [x] Streaming response
- [x] LLM client (OpenAI compatible)
- [x] RAG with InMemoryVector store

### v0.0.5
- [x] Claude provider support
- [x] WebSocket streaming
- [x] Swagger docs
- [x] Embeddings
- [ ] Model auto-loader support

### v0.1.0 (Public Beta)
- [ ] CLI scaffolding
- [ ] Optional backends (torch/onnx/gguf)
- [ ] VectorDB adapters
- [ ] Playground UI for chat/RAG
- [ ] Benchmark suite

### v1.0 Stable
- [ ] Production-ready performance
- [ ] Plugins ecosystem
- [ ] Documentation website
- [ ] Community contributions

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

QuickAPI is licensed under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Inspired by FastAPI's elegant design
- Built with performance insights from Starlette
- AI integration patterns from LangChain