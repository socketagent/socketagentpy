"""
Example authenticated todo API using socket-agent with socketagent.id integration.

This example demonstrates:
1. Setting up a FastAPI app with socket-agent descriptors
2. Adding authentication middleware
3. Protecting endpoints with @auth_required decorator
4. Integration with socketagent.id for token validation

To run this example:
1. Set environment variable: export SOCKETAGENT_SERVER_ID="your_server_id"
2. Run this API: `python main.py`
3. Your API will be discoverable at https://socketagent.io/auth/your_server_id
"""

import os
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

from socket_agent import (
    SocketAgentMiddleware,
    SocketAgentAuthMiddleware,
    socket,
    auth_required,
    get_current_user
)


# Pydantic models
class TodoCreate(BaseModel):
    text: str
    priority: str = "medium"


class Todo(BaseModel):
    id: int
    text: str
    priority: str
    completed: bool = False
    user_id: int


class User(BaseModel):
    id: int
    username: str
    email: str = None


# Create FastAPI app
app = FastAPI(title="Authenticated Todo API")

# Get server_id from environment variable
# Get this from https://socketagent.io/dashboard.html after subscribing
SERVER_ID = os.getenv("SOCKETAGENT_SERVER_ID")

# Add authentication middleware first
SocketAgentAuthMiddleware(
    app,
    identity_service_url="https://socketagent.io",
    server_id=SERVER_ID,
    audience="todo-api",
    cache_ttl=300
)

# Add socket-agent middleware
SocketAgentMiddleware(
    app,
    name="Authenticated Todo API",
    description="A simple todo API with socketagent.id authentication",
    auth_server_id=SERVER_ID,
    auth_identity_service_url="https://socketagent.io"
)

# In-memory storage (replace with database in production)
todos_db = {}
next_todo_id = 1


@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {"status": "healthy"}


@app.get("/todos")
@socket.describe(
    "List all todos for the authenticated user",
    response_schema={
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "text": {"type": "string"},
                "priority": {"type": "string"},
                "completed": {"type": "boolean"},
                "user_id": {"type": "integer"}
            }
        }
    }
)
@auth_required()
async def list_todos(user = Depends(get_current_user)):
    """List todos for authenticated user (anonymous or with user account)."""
    user_id = user.id if user else 0
    # Filter by user_id (0 for anonymous tokens)
    user_todos = [todo for todo in todos_db.values() if todo["user_id"] == user_id]
    return user_todos


@app.post("/todos")
@socket.describe(
    "Create a new todo item",
    request_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Todo item text"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"}
        },
        "required": ["text"]
    },
    response_schema={
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "text": {"type": "string"},
            "priority": {"type": "string"},
            "completed": {"type": "boolean"},
            "user_id": {"type": "integer"}
        }
    }
)
@auth_required(scopes=["write:todos"])
async def create_todo(todo_data: TodoCreate, user = Depends(get_current_user)):
    """Create a new todo item for authenticated user."""
    global next_todo_id

    todo = {
        "id": next_todo_id,
        "text": todo_data.text,
        "priority": todo_data.priority,
        "completed": False,
        "user_id": user.id if user else 0  # Use 0 for anonymous tokens
    }

    todos_db[next_todo_id] = todo
    next_todo_id += 1

    return todo


@app.put("/todos/{todo_id}")
@socket.describe(
    "Update a todo item",
    request_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            "completed": {"type": "boolean"}
        }
    },
    response_schema={
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "text": {"type": "string"},
            "priority": {"type": "string"},
            "completed": {"type": "boolean"},
            "user_id": {"type": "integer"}
        }
    }
)
@auth_required(scopes=["write:todos"])
async def update_todo(
    todo_id: int,
    todo_data: TodoCreate,
    user = Depends(get_current_user)
):
    """Update a todo item (only owner can update)."""
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")

    todo = todos_db[todo_id]
    user_id = user.id if user else 0
    if todo["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this todo")

    # Update fields
    todo.update({
        "text": todo_data.text,
        "priority": todo_data.priority
    })

    return todo


@app.delete("/todos/{todo_id}")
@socket.describe("Delete a todo item")
@auth_required(scopes=["write:todos"])
async def delete_todo(todo_id: int, user = Depends(get_current_user)):
    """Delete a todo item (only owner can delete)."""
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")

    todo = todos_db[todo_id]
    user_id = user.id if user else 0
    if todo["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this todo")

    del todos_db[todo_id]
    return {"message": "Todo deleted successfully"}


if __name__ == "__main__":
    import uvicorn

    print("Starting authenticated todo API...")
    if SERVER_ID:
        print(f"Server ID: {SERVER_ID}")
        print(f"Discovery URL: https://socketagent.io/auth/{SERVER_ID}")
    else:
        print("⚠️  WARNING: SOCKETAGENT_SERVER_ID not set!")
        print("   Get your server_id from: https://socketagent.io/dashboard.html")
        print("   Set it with: export SOCKETAGENT_SERVER_ID='your_server_id'")
    print("API will be available at http://localhost:8001")
    print("Socket agent descriptor at http://localhost:8001/.well-known/socket-agent")

    uvicorn.run(app, host="0.0.0.0", port=8001)