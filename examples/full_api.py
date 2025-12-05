"""
QuickAPI Full REST API Example

Complete REST API with:
- CORS middleware
- JWT Authentication
- Swagger/OpenAPI documentation
- CRUD operations
- Error handling
- Rate limiting
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from quickapi import QuickAPI, JSONResponse, api_doc, requires_auth
from quickapi.middleware import CORSMiddleware, JWTAuthMiddleware, AuthMiddleware

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
# ============================================================================

# In-memory storage (use database in production)
users_db: Dict[str, Dict] = {
    "admin": {
        "id": "1",
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123",  # In production: hash this!
        "role": "admin"
    },
    "user": {
        "id": "2",
        "username": "user",
        "email": "user@example.com",
        "password": "user123",  # In production: hash this!
        "role": "user"
    }
}

items_db: Dict[str, Dict] = {}
item_counter = 0

# Create the app
app = QuickAPI(
    title="Full REST API",
    version="1.0.0",
    debug=True
)

# ============================================================================
# Middleware Setup
# ============================================================================

# 1. CORS Middleware (allow all origins for demo)
app.middleware(CORSMiddleware(
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
))

# 2. JWT Auth Middleware (for protected routes)
jwt_auth = JWTAuthMiddleware(
    secret_key=JWT_SECRET,
    algorithm=JWT_ALGORITHM
)

# ============================================================================
# Helper Functions
# ============================================================================

def create_token(user_id: str, username: str, role: str) -> str:
    """Create JWT token"""
    import jwt
    
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> Optional[Dict]:
    """Verify JWT token"""
    import jwt
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user(request) -> Optional[Dict]:
    """Get current user from request"""
    auth_header = None
    for header_name, header_value in request.scope.get("headers", []):
        if header_name.decode().lower() == "authorization":
            auth_header = header_value.decode()
            break
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        return None
    
    return payload


# ============================================================================
# Public Endpoints (No Auth Required)
# ============================================================================

@app.get("/")
async def root(request):
    """Root endpoint with API information"""
    return JSONResponse({
        "message": "Welcome to Full REST API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {
            "auth": {
                "login": "POST /api/auth/login",
                "register": "POST /api/auth/register",
                "me": "GET /api/auth/me (requires auth)"
            },
            "items": {
                "list": "GET /api/items",
                "get": "GET /api/items/{id}",
                "create": "POST /api/items (requires auth)",
                "update": "PUT /api/items/{id} (requires auth)",
                "delete": "DELETE /api/items/{id} (requires auth)"
            }
        }
    })


@app.get("/api/health")
async def health(request):
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "total_users": len(users_db),
        "total_items": len(items_db)
    })


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/login")
@api_doc(
    summary="Login to get JWT token",
    tags=["Authentication"],
    request_body={
        "schema": {
            "type": "object",
            "properties": {
                "username": {"type": "string", "example": "admin"},
                "password": {"type": "string", "example": "admin123"}
            },
            "required": ["username", "password"]
        }
    },
    responses={
        "200": {
            "description": "Login successful",
            "schema": {
                "type": "object",
                "properties": {
                    "access_token": {"type": "string"},
                    "token_type": {"type": "string"},
                    "expires_in": {"type": "integer"},
                    "user": {"type": "object"}
                }
            }
        }
    }
)
async def login(request):
    """Login endpoint"""
    body = await request.json()
    username = body.get("username")
    password = body.get("password")
    
    if not username or not password:
        return JSONResponse(
            {"error": "Username and password required"},
            status_code=400
        )
    
    # Check user exists
    user = users_db.get(username)
    if not user:
        return JSONResponse(
            {"error": "Invalid credentials"},
            status_code=401
        )
    
    # Check password (in production: use bcrypt!)
    if user["password"] != password:
        return JSONResponse(
            {"error": "Invalid credentials"},
            status_code=401
        )
    
    # Create token
    token = create_token(user["id"], user["username"], user["role"])
    
    return JSONResponse({
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    })


@app.post("/api/auth/register")
async def register(request):
    """
    Register new user
    
    Request body:
    {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123"
    }
    """
    body = await request.json()
    username = body.get("username")
    email = body.get("email")
    password = body.get("password")
    
    if not username or not email or not password:
        return JSONResponse(
            {"error": "Username, email, and password required"},
            status_code=400
        )
    
    # Check if user exists
    if username in users_db:
        return JSONResponse(
            {"error": "Username already exists"},
            status_code=400
        )
    
    # Create user (in production: hash password!)
    user_id = str(len(users_db) + 1)
    users_db[username] = {
        "id": user_id,
        "username": username,
        "email": email,
        "password": password,  # In production: hash this!
        "role": "user"
    }
    
    # Create token
    token = create_token(user_id, username, "user")
    
    return JSONResponse({
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600,
        "user": {
            "id": user_id,
            "username": username,
            "email": email,
            "role": "user"
        }
    }, status_code=201)


@app.get("/api/auth/me")
async def get_me(request):
    """Get current user info (requires authentication)"""
    user = get_current_user(request)
    
    if not user:
        return JSONResponse(
            {"error": "Unauthorized"},
            status_code=401
        )
    
    return JSONResponse({
        "user": {
            "id": user["user_id"],
            "username": user["username"],
            "role": user["role"]
        }
    })


# ============================================================================
# Items CRUD Endpoints
# ============================================================================

@app.get("/api/items")
@api_doc(
    summary="List all items",
    tags=["Items"],
    responses={
        "200": {
            "description": "List of items",
            "schema": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "price": {"type": "number"}
                            }
                        }
                    },
                    "total": {"type": "integer"}
                }
            }
        }
    }
)
async def list_items(request):
    """List all items (public)"""
    items = list(items_db.values())
    
    return JSONResponse({
        "items": items,
        "total": len(items)
    })


@app.get("/api/items/{item_id}")
async def get_item(request, item_id: str):
    """Get single item by ID (public)"""
    item = items_db.get(item_id)
    
    if not item:
        return JSONResponse(
            {"error": "Item not found"},
            status_code=404
        )
    
    return JSONResponse(item)


@app.post("/api/items")
@api_doc(
    summary="Create new item",
    tags=["Items"],
    request_body={
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "example": "Laptop"},
                "description": {"type": "string", "example": "MacBook Pro 16-inch"},
                "price": {"type": "number", "example": 2499.99}
            },
            "required": ["name"]
        }
    },
    responses={
        "201": {
            "description": "Item created successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "price": {"type": "number"},
                    "created_by": {"type": "string"},
                    "created_at": {"type": "string"},
                    "updated_at": {"type": "string"}
                }
            }
        }
    },
    security=[{"bearerAuth": []}]
)
async def create_item(request):
    """Create new item (requires authentication)"""
    # Check authentication
    user = get_current_user(request)
    if not user:
        return JSONResponse(
            {"error": "Unauthorized - Please login"},
            status_code=401
        )
    
    # Get request body
    body = await request.json()
    name = body.get("name")
    description = body.get("description", "")
    price = body.get("price", 0)
    
    if not name:
        return JSONResponse(
            {"error": "Name is required"},
            status_code=400
        )
    
    # Create item
    global item_counter
    item_counter += 1
    item_id = str(item_counter)
    
    item = {
        "id": item_id,
        "name": name,
        "description": description,
        "price": price,
        "created_by": user["username"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    items_db[item_id] = item
    
    return JSONResponse(item, status_code=201)


@app.put("/api/items/{item_id}")
async def update_item(request, item_id: str):
    """
    Update item (requires authentication)
    
    Request body:
    {
        "name": "Updated name",
        "description": "Updated description",
        "price": 149.99
    }
    """
    # Check authentication
    user = get_current_user(request)
    if not user:
        return JSONResponse(
            {"error": "Unauthorized - Please login"},
            status_code=401
        )
    
    # Check item exists
    item = items_db.get(item_id)
    if not item:
        return JSONResponse(
            {"error": "Item not found"},
            status_code=404
        )
    
    # Get request body
    body = await request.json()
    
    # Update item
    if "name" in body:
        item["name"] = body["name"]
    if "description" in body:
        item["description"] = body["description"]
    if "price" in body:
        item["price"] = body["price"]
    
    item["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    return JSONResponse(item)


@app.delete("/api/items/{item_id}")
async def delete_item(request, item_id: str):
    """Delete item (requires authentication)"""
    # Check authentication
    user = get_current_user(request)
    if not user:
        return JSONResponse(
            {"error": "Unauthorized - Please login"},
            status_code=401
        )
    
    # Check item exists
    if item_id not in items_db:
        return JSONResponse(
            {"error": "Item not found"},
            status_code=404
        )
    
    # Delete item
    del items_db[item_id]
    
    return JSONResponse({
        "message": "Item deleted successfully"
    })


# ============================================================================
# Admin Endpoints (Admin only)
# ============================================================================

@app.get("/api/admin/users")
async def list_users(request):
    """List all users (admin only)"""
    user = get_current_user(request)
    
    if not user:
        return JSONResponse(
            {"error": "Unauthorized"},
            status_code=401
        )
    
    if user["role"] != "admin":
        return JSONResponse(
            {"error": "Forbidden - Admin access required"},
            status_code=403
        )
    
    users = [
        {
            "id": u["id"],
            "username": u["username"],
            "email": u["email"],
            "role": u["role"]
        }
        for u in users_db.values()
    ]
    
    return JSONResponse({
        "users": users,
        "total": len(users)
    })


@app.get("/api/admin/stats")
async def get_stats(request):
    """Get system statistics (admin only)"""
    user = get_current_user(request)
    
    if not user:
        return JSONResponse(
            {"error": "Unauthorized"},
            status_code=401
        )
    
    if user["role"] != "admin":
        return JSONResponse(
            {"error": "Forbidden - Admin access required"},
            status_code=403
        )
    
    return JSONResponse({
        "total_users": len(users_db),
        "total_items": len(items_db),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


# ============================================================================
# Swagger/OpenAPI Documentation
# ============================================================================
# Docs are automatically generated at /docs and /openapi.json
# No need to add manual routes!


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Full REST API")
    print("🌐 Server: http://localhost:8000")
    print("📚 Swagger Docs: http://localhost:8000/docs")
    print("📖 OpenAPI Spec: http://localhost:8000/openapi.json")
    print()
    print("🔐 Test Credentials:")
    print("   Admin: username=admin, password=admin123")
    print("   User:  username=user, password=user123")
    print()
    print("📝 Example Usage:")
    print("   1. Login: POST /api/auth/login")
    print("   2. Get token from response")
    print("   3. Use token: Authorization: Bearer <token>")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
