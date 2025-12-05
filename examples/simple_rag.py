"""
QuickAPI Simple RAG with DeepSeek

Minimal RAG (Retrieval-Augmented Generation) example:
1. Upload documents
2. Store as vectors (embeddings)
3. Chat with your documents
4. AI answers based on document context

No complex dependencies - just httpx and basic math!
"""

import os
import httpx
import json
import math
from typing import List, Dict, Tuple
from quickapi import QuickAPI, JSONResponse
from quickapi.middleware import CORSMiddleware

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# CONFIGURATION - Loaded from .env file
# ============================================================================
# Vercel AI Gateway
GATEWAY_URL = "https://ai-gateway.vercel.sh/v1"
GATEWAY_API_KEY = os.getenv("VERCEL_GATEWAY_API_KEY", "your-vercel-gateway-api-key-here")

# Models (via Vercel Gateway)
CHAT_MODEL = os.getenv("CHAT_MODEL", "deepseek/deepseek-chat")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
# ============================================================================

# In-memory storage
documents: List[Dict] = []  # Stores: {id, text, embedding, metadata}
conversations: Dict[str, List[Dict[str, str]]] = {}

# Create the app
app = QuickAPI(title="Simple RAG", version="1.0.0", debug=True)
app.middleware(CORSMiddleware(allow_origins=["*"]))


# ============================================================================
# Vector/Embedding Functions
# ============================================================================

async def get_embedding(text: str) -> List[float]:
    """Get embedding vector for text using Vercel AI Gateway"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GATEWAY_URL}/embeddings",
            headers={
                "Authorization": f"Bearer {GATEWAY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": EMBEDDING_MODEL,
                "input": text
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise Exception(f"Embedding API Error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result["data"][0]["embedding"]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


def search_documents(query_embedding: List[float], top_k: int = 3) -> List[Dict]:
    """Search documents by similarity to query embedding"""
    if not documents:
        return []
    
    # Calculate similarity scores
    results = []
    for doc in documents:
        similarity = cosine_similarity(query_embedding, doc["embedding"])
        results.append({
            "id": doc["id"],
            "text": doc["text"],
            "metadata": doc.get("metadata", {}),
            "similarity": similarity
        })
    
    # Sort by similarity (highest first)
    results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Return top K results
    return results[:top_k]


async def call_llm(messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
    """Call LLM via Vercel AI Gateway"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GATEWAY_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {GATEWAY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": CHAT_MODEL,
                "messages": messages,
                "temperature": temperature,
                "stream": False
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]


# ============================================================================
# Document Management Endpoints
# ============================================================================

@app.post("/api/documents")
async def upload_document(request):
    """Upload a document and store its embedding"""
    body = await request.json()
    text = body.get("text", "")
    metadata = body.get("metadata", {})
    
    if not text:
        return JSONResponse({"error": "Text is required"}, status_code=400)
    
    try:
        # Generate embedding
        embedding = await get_embedding(text)
        
        # Store document
        doc_id = f"doc_{len(documents) + 1}"
        doc = {
            "id": doc_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata
        }
        documents.append(doc)
        
        return JSONResponse({
            "id": doc_id,
            "text": text[:100] + "..." if len(text) > 100 else text,
            "metadata": metadata,
            "embedding_size": len(embedding)
        })
    
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to process document: {str(e)}"},
            status_code=500
        )


@app.get("/api/documents")
async def list_documents(request):
    """List all documents"""
    return JSONResponse({
        "documents": [
            {
                "id": doc["id"],
                "text": doc["text"][:100] + "..." if len(doc["text"]) > 100 else doc["text"],
                "metadata": doc.get("metadata", {})
            }
            for doc in documents
        ],
        "total": len(documents)
    })


@app.delete("/api/documents/{doc_id}")
async def delete_document(request, doc_id: str):
    """Delete a document"""
    global documents
    documents = [doc for doc in documents if doc["id"] != doc_id]
    return JSONResponse({"message": "Document deleted"})


@app.delete("/api/documents")
async def clear_documents(request):
    """Clear all documents"""
    global documents
    documents = []
    return JSONResponse({"message": "All documents cleared"})


# ============================================================================
# RAG Chat Endpoints
# ============================================================================

@app.post("/api/rag/search")
async def search(request):
    """Search documents by query"""
    body = await request.json()
    query = body.get("query", "")
    top_k = body.get("top_k", 3)
    
    if not query:
        return JSONResponse({"error": "Query is required"}, status_code=400)
    
    try:
        # Get query embedding
        query_embedding = await get_embedding(query)
        
        # Search documents
        results = search_documents(query_embedding, top_k)
        
        return JSONResponse({
            "query": query,
            "results": results
        })
    
    except Exception as e:
        return JSONResponse(
            {"error": f"Search failed: {str(e)}"},
            status_code=500
        )


@app.post("/api/rag/chat/{conversation_id}")
async def rag_chat(request, conversation_id: str):
    """Chat with RAG - AI answers based on document context"""
    # Get or create conversation
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    
    # Get message from request
    body = await request.json()
    message = body.get("message", "")
    
    if not message:
        return JSONResponse({"error": "Message is required"}, status_code=400)
    
    if not documents:
        return JSONResponse(
            {"error": "No documents uploaded. Please upload documents first."},
            status_code=400
        )
    
    try:
        # 1. Get query embedding
        query_embedding = await get_embedding(message)
        
        # 2. Search relevant documents
        relevant_docs = search_documents(query_embedding, top_k=3)
        
        # 3. Build context from relevant documents
        context = "\n\n".join([
            f"Document {i+1} (similarity: {doc['similarity']:.2f}):\n{doc['text']}"
            for i, doc in enumerate(relevant_docs)
        ])
        
        # 4. Add user message to history
        conversations[conversation_id].append({
            "role": "user",
            "content": message
        })
        
        # 5. Build prompt with context
        system_prompt = f"""You are a helpful AI assistant. Answer questions based on the provided context.

Context from documents:
{context}

Instructions:
- Answer based on the context above
- If the answer is not in the context, say "I don't have enough information to answer that"
- Be concise and accurate
- Cite which document you're using if relevant"""
        
        # 6. Build messages for API
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversations[conversation_id])
        
        # 7. Get AI response
        response = await call_llm(messages, temperature=0.7)
        
        # 8. Add assistant response to history
        conversations[conversation_id].append({
            "role": "assistant",
            "content": response
        })
        
        return JSONResponse({
            "conversation_id": conversation_id,
            "user_message": message,
            "assistant_response": response,
            "relevant_documents": [
                {
                    "id": doc["id"],
                    "similarity": doc["similarity"],
                    "text": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"]
                }
                for doc in relevant_docs
            ],
            "message_count": len(conversations[conversation_id])
        })
    
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to get AI response: {str(e)}"},
            status_code=500
        )


# ============================================================================
# Web UI
# ============================================================================

@app.get("/")
async def root(request):
    """Serve the RAG chatbot HTML page"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>QuickAPI RAG Chatbot</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 20px;
            height: 85vh;
        }
        .panel {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 { font-size: 20px; margin-bottom: 5px; }
        .header p { font-size: 12px; opacity: 0.9; }
        .content {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }
        .upload-area {
            border: 2px dashed #ddd;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        }
        textarea {
            width: 100%;
            min-height: 100px;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            resize: vertical;
            margin-bottom: 10px;
        }
        button {
            padding: 10px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
        }
        button:hover { opacity: 0.9; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .doc-list {
            margin-top: 20px;
        }
        .doc-item {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 13px;
        }
        .doc-item .doc-id {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 4px;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 16px;
            display: flex;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user { justify-content: flex-end; }
        .message.assistant { justify-content: flex-start; }
        .message-bubble {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
            white-space: pre-wrap;
        }
        .message.user .message-bubble {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .message.assistant .message-bubble {
            background: white;
            color: #333;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .sources {
            font-size: 11px;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid rgba(0,0,0,0.1);
            color: #666;
        }
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        .input-group {
            display: flex;
            gap: 10px;
        }
        #messageInput {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 24px;
            font-size: 14px;
            outline: none;
        }
        #messageInput:focus { border-color: #667eea; }
        .status {
            text-align: center;
            padding: 8px;
            font-size: 12px;
            color: #666;
        }
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #999;
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
            font-size: 14px;
        }
        .success {
            background: #efe;
            color: #3c3;
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Left Panel: Document Upload -->
        <div class="panel">
            <div class="header">
                <h1>📚 Documents</h1>
                <p>Upload documents to chat with</p>
            </div>
            <div class="content">
                <div class="upload-area">
                    <h3>Upload Document</h3>
                    <textarea id="docText" placeholder="Paste your document text here..."></textarea>
                    <button onclick="uploadDocument()">Upload</button>
                    <button onclick="clearDocuments()" style="background: #dc3545; margin-left: 10px;">Clear All</button>
                </div>
                <div id="uploadStatus"></div>
                <div class="doc-list">
                    <h4>Uploaded Documents (<span id="docCount">0</span>)</h4>
                    <div id="docList"></div>
                </div>
            </div>
        </div>
        
        <!-- Right Panel: Chat -->
        <div class="panel">
            <div class="header">
                <h1>🤖 RAG Chat</h1>
                <p>Ask questions about your documents</p>
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="empty-state">
                    <h2>👋 Welcome to RAG Chat!</h2>
                    <p>Upload documents on the left, then ask questions about them</p>
                </div>
            </div>
            <div class="input-area">
                <div class="status" id="status"></div>
                <div class="input-group">
                    <input 
                        type="text" 
                        id="messageInput" 
                        placeholder="Ask a question about your documents..." 
                        autocomplete="off"
                    />
                    <button id="sendButton" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const conversationId = 'conv_' + Date.now();
        let isProcessing = false;
        
        // Upload document
        async function uploadDocument() {
            const text = document.getElementById('docText').value.trim();
            if (!text) {
                showStatus('Please enter document text', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/documents', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('docText').value = '';
                    showStatus('Document uploaded successfully!', 'success');
                    loadDocuments();
                } else {
                    showStatus('Error: ' + data.error, 'error');
                }
            } catch (error) {
                showStatus('Error: ' + error.message, 'error');
            }
        }
        
        // Load documents
        async function loadDocuments() {
            try {
                const response = await fetch('/api/documents');
                const data = await response.json();
                
                document.getElementById('docCount').textContent = data.total;
                
                const docList = document.getElementById('docList');
                docList.innerHTML = '';
                
                data.documents.forEach(doc => {
                    const div = document.createElement('div');
                    div.className = 'doc-item';
                    div.innerHTML = `
                        <div class="doc-id">${doc.id}</div>
                        <div>${doc.text}</div>
                    `;
                    docList.appendChild(div);
                });
            } catch (error) {
                console.error('Error loading documents:', error);
            }
        }
        
        // Clear documents
        async function clearDocuments() {
            if (!confirm('Clear all documents?')) return;
            
            try {
                await fetch('/api/documents', { method: 'DELETE' });
                showStatus('All documents cleared', 'success');
                loadDocuments();
            } catch (error) {
                showStatus('Error: ' + error.message, 'error');
            }
        }
        
        // Send message
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message || isProcessing) return;
            
            isProcessing = true;
            document.getElementById('sendButton').disabled = true;
            input.disabled = true;
            
            addMessage(message, 'user');
            input.value = '';
            showLoading(true);
            
            try {
                const response = await fetch(`/api/rag/chat/${conversationId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    addMessage(data.assistant_response, 'assistant', data.relevant_documents);
                } else {
                    addError(data.error);
                }
            } catch (error) {
                addError('Error: ' + error.message);
            } finally {
                isProcessing = false;
                document.getElementById('sendButton').disabled = false;
                input.disabled = false;
                input.focus();
                showLoading(false);
            }
        }
        
        // Add message to chat
        function addMessage(text, sender, sources = null) {
            const emptyState = document.querySelector('.empty-state');
            if (emptyState) emptyState.remove();
            
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const bubbleDiv = document.createElement('div');
            bubbleDiv.className = 'message-bubble';
            bubbleDiv.textContent = text;
            
            if (sources && sources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'sources';
                sourcesDiv.innerHTML = '📄 Sources: ' + sources.map(s => 
                    `${s.id} (${(s.similarity * 100).toFixed(0)}%)`
                ).join(', ');
                bubbleDiv.appendChild(sourcesDiv);
            }
            
            messageDiv.appendChild(bubbleDiv);
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function addError(message) {
            const chatMessages = document.getElementById('chatMessages');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = message;
            chatMessages.appendChild(errorDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('uploadStatus');
            statusDiv.className = type;
            statusDiv.textContent = message;
            setTimeout(() => statusDiv.textContent = '', 3000);
        }
        
        function showLoading(show) {
            document.getElementById('status').textContent = show ? '🤔 AI is thinking...' : '';
        }
        
        // Event listeners
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
        
        // Load documents on start
        loadDocuments();
    </script>
</body>
</html>
    """
    
    from quickapi.response import HTMLResponse
    return HTMLResponse(html_content)


@app.get("/api/health")
async def health(request):
    """Health check endpoint"""
    is_configured = GATEWAY_API_KEY and GATEWAY_API_KEY != "your-vercel-gateway-api-key-here"
    return JSONResponse({
        "status": "healthy",
        "total_documents": len(documents),
        "total_conversations": len(conversations),
        "chat_model": CHAT_MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "gateway": "Vercel AI Gateway",
        "api_configured": is_configured
    })


if __name__ == "__main__":
    import uvicorn
    print("🤖 Starting QuickAPI Simple RAG")
    print("🌐 Open your browser: http://localhost:8000")
    print(f"🧠 Chat Model: {CHAT_MODEL}")
    print(f"📊 Embedding: {EMBEDDING_MODEL}")
    print(f"🌐 Gateway: Vercel AI Gateway")
    print()
    if GATEWAY_API_KEY == "your-vercel-gateway-api-key-here":
        print("⚠️  WARNING: Please set your Vercel AI Gateway API key in the code!")
        print("   Edit GATEWAY_API_KEY variable at the top of simple_rag.py")
        print("   Get key from: https://vercel.com/docs/ai-gateway")
    else:
        print("✅ API key configured")
    print()
    print("📚 How to use:")
    print("   1. Upload documents (left panel)")
    print("   2. Ask questions about them (right panel)")
    print("   3. AI answers based on document context")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000)
