# FastAPI Quick Reference

## What is FastAPI?

FastAPI is a modern, fast web framework for building APIs with Python based on standard Python type hints. It is one of the fastest Python frameworks available, on par with NodeJS and Go. FastAPI is built on top of Starlette for the web parts and Pydantic for the data parts.

Key features include automatic API documentation with Swagger UI, data validation using Pydantic models, async support out of the box, and dependency injection.

## Installation

To install FastAPI, use pip:

```bash
pip install fastapi[standard]
```

This installs FastAPI along with uvicorn as the ASGI server. Uvicorn is the recommended server for running FastAPI applications in both development and production.

## Creating Your First App

A minimal FastAPI application looks like this:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

Run it with: `uvicorn main:app --reload`

The `--reload` flag enables auto-restart when code changes. Only use it during development, not in production.

## Path Parameters

Path parameters are parts of the URL that are variable. They are declared in the path and received as function arguments:

```python
@app.get("/users/{user_id}")
async def read_user(user_id: int):
    return {"user_id": user_id}
```

FastAPI automatically validates that `user_id` is an integer. If someone sends `/users/abc`, they get a 422 Validation Error with a clear message.

## Query Parameters

Query parameters are the key-value pairs that appear after `?` in a URL. In FastAPI, any function parameter that is not a path parameter is automatically treated as a query parameter:

```python
@app.get("/items")
async def read_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}
```

This creates an endpoint like `/items?skip=0&limit=10`. Default values make parameters optional.

## Request Body with Pydantic

For POST/PUT requests, you define the expected data structure using Pydantic models:

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    description: str | None = None

@app.post("/items")
async def create_item(item: Item):
    return item
```

FastAPI automatically validates the incoming JSON against the model, generates documentation, and provides editor support.

## Dependency Injection

FastAPI has a powerful dependency injection system. Dependencies are functions that are called before your endpoint:

```python
from fastapi import Depends

async def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

@app.get("/users")
async def read_users(db = Depends(get_db)):
    return db.query("SELECT * FROM users")
```

Dependencies can depend on other dependencies, creating a tree. FastAPI resolves them automatically and handles cleanup with `yield`.

## Error Handling

Use HTTPException to return error responses:

```python
from fastapi import HTTPException

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]
```

You can also create custom exception handlers for specific error types.

## Middleware

Middleware runs before every request and after every response. Common uses include CORS, authentication, and logging:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Background Tasks

For operations that don't need to complete before sending the response, use BackgroundTasks:

```python
from fastapi import BackgroundTasks

@app.post("/send-email")
async def send_email(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email_task, "user@example.com")
    return {"message": "Email will be sent"}
```

## Testing

FastAPI provides a TestClient for testing endpoints without running a server:

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
```

TestClient uses httpx internally and supports both sync and async testing.