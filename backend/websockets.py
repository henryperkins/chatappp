# WebSocket handling for real-time streaming
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set, Optional
import asyncio
import json
from .llm_client import LLMClient
from .database import get_db, ChatMessage
from .models import StreamChunk
from sqlalchemy.orm import Session
from datetime import datetime
import traceback


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.abort_flags: Dict[str, asyncio.Event] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.abort_flags[client_id] = asyncio.Event()

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.abort_flags:
            del self.abort_flags[client_id]

    async def send_chunk(self, client_id: str, chunk: StreamChunk):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(chunk.dict())

    def abort_generation(self, client_id: str):
        if client_id in self.abort_flags:
            self.abort_flags[client_id].set()

    def is_aborted(self, client_id: str) -> bool:
        if client_id in self.abort_flags:
            return self.abort_flags[client_id].is_set()
        return False


manager = ConnectionManager()


async def handle_chat_message(
    websocket: WebSocket,
    client_id: str,
    message: dict,
    db: Session,
    llm_client: LLMClient,
):
    try:
        # Reset abort flag
        if client_id in manager.abort_flags:
            manager.abort_flags[client_id].clear()

        content = message.get("content", "")
        command = message.get("command")
        temperature = message.get("temperature", 0.7)
        max_tokens = message.get("max_tokens", 2048)

        # Save user message
        user_msg = ChatMessage(
            role="user",
            content=content,
            model=llm_client.model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        db.add(user_msg)
        db.commit()

        # Get recent messages for context
        recent_messages = (
            db.query(ChatMessage).order_by(ChatMessage.timestamp.desc()).limit(10).all()
        )

        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(recent_messages)
        ]

        # Stream response
        full_response = ""
        async for chunk in llm_client.generate_stream(
            messages=messages,
            command=command,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            if manager.is_aborted(client_id):
                await manager.send_chunk(
                    client_id, StreamChunk(type="error", error="Generation aborted")
                )
                break

            full_response += chunk
            await manager.send_chunk(client_id, StreamChunk(type="content", data=chunk))

            # Small delay to avoid overwhelming the client
            await asyncio.sleep(0.01)

        # Save assistant response if not aborted
        if not manager.is_aborted(client_id) and full_response:
            assistant_msg = ChatMessage(
                role="assistant",
                content=full_response,
                model=llm_client.model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            db.add(assistant_msg)
            db.commit()

        await manager.send_chunk(client_id, StreamChunk(type="done"))

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        await manager.send_chunk(client_id, StreamChunk(type="error", error=error_msg))
        traceback.print_exc()
