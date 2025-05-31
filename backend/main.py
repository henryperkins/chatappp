# Main FastAPI application
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import asyncio
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.database import init_db, get_db, ChatMessage
from backend.auth import auth_manager, get_current_user, verify_csrf_token
from backend.models import *
from backend.config import settings
from backend.websockets import manager, handle_chat_message
from backend.llm_client import LLMClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    pass


app = FastAPI(title="Minimal AI Coding Chat", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create LLM client instance
llm_client = LLMClient()

# Serve static frontend files
static_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


# Auth endpoints
@app.post("/api/auth/login")
async def login(request: Request, response: Response, login_data: LoginRequest):
    # Rate limiting
    client_ip = request.client.host
    if not auth_manager.check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many login attempts")

    # Verify credentials
    if (
        login_data.username != settings.admin_username
        or not auth_manager.verify_password(
            login_data.password, auth_manager.get_password_hash(settings.admin_password)
        )
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create session
    token = auth_manager.create_session_token(login_data.username)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.session_expire_minutes * 60,
    )

    return {
        "status": "success",
        "csrf_token": auth_manager.verify_session_token(token)["csrf"],
    }


@app.post("/api/auth/logout")
async def logout(response: Response, _: str = Depends(get_current_user)):
    response.delete_cookie("session_token")
    return {"status": "success"}


# Chat endpoints
@app.get("/api/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
):
    query = db.query(ChatMessage)

    if search:
        query = query.filter(ChatMessage.content.contains(search))

    total = query.count()
    messages = (
        query.order_by(ChatMessage.timestamp.desc()).offset(offset).limit(limit).all()
    )

    return ChatHistoryResponse(
        messages=[ChatMessageResponse.from_orm(msg) for msg in reversed(messages)],
        total=total,
    )


@app.delete("/api/chat/history")
async def clear_chat_history(
    db: Session = Depends(get_db), _: str = Depends(get_current_user)
):
    db.query(ChatMessage).delete()
    db.commit()
    return {"status": "success"}


# Settings endpoints
@app.get("/api/settings")
async def get_settings(_: str = Depends(get_current_user)):
    return {
        "model": settings.openai_model,
        "max_tokens": settings.max_tokens,
        "temperature": settings.temperature,
        "provider": settings.openai_provider,
    }


@app.post("/api/settings")
async def update_settings(update: SettingsUpdate, _: str = Depends(get_current_user)):
    if update.model:
        settings.openai_model = update.model
        llm_client.model = update.model
    if update.max_tokens is not None:
        settings.max_tokens = update.max_tokens
    if update.temperature is not None:
        settings.temperature = update.temperature

    return {"status": "success"}


# WebSocket endpoint
@app.websocket("/ws/chat/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, client_id: str, db: Session = Depends(get_db)
):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "message":
                await handle_chat_message(websocket, client_id, data, db, llm_client)
            elif data.get("type") == "abort":
                manager.abort_generation(client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(client_id)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
