# WebSocket tests
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi import WebSocket
from ..websockets import ConnectionManager, handle_chat_message
from ..models import StreamChunk


class TestWebSockets:

    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        ws = Mock(spec=WebSocket)
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connection_management(self, manager, mock_websocket):
        # Test connect
        await manager.connect(mock_websocket, "test-client")
        assert "test-client" in manager.active_connections
        assert "test-client" in manager.abort_flags

        # Test disconnect
        manager.disconnect("test-client")
        assert "test-client" not in manager.active_connections
        assert "test-client" not in manager.abort_flags

    @pytest.mark.asyncio
    async def test_send_chunk(self, manager, mock_websocket):
        await manager.connect(mock_websocket, "test-client")

        chunk = StreamChunk(type="content", data="Hello")
        await manager.send_chunk("test-client", chunk)

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "content"
        assert call_args["data"] == "Hello"

    def test_abort_generation(self, manager):
        manager.abort_flags["test-client"] = asyncio.Event()

        assert not manager.is_aborted("test-client")
        manager.abort_generation("test-client")
        assert manager.is_aborted("test-client")

    @pytest.mark.asyncio
    async def test_handle_chat_message(self, manager, mock_websocket):
        mock_db = Mock()
        mock_llm_client = Mock()

        # Mock the stream response
        async def mock_stream(*args, **kwargs):
            yield "Hello"
            yield " world"

        mock_llm_client.generate_stream = mock_stream

        with patch("backend.websockets.manager", manager):
            await manager.connect(mock_websocket, "test-client")

            message = {
                "content": "Test message",
                "command": None,
                "temperature": 0.7,
                "max_tokens": 2048,
            }

            await handle_chat_message(
                mock_websocket, "test-client", message, mock_db, mock_llm_client
            )

            # Verify database operations
            assert mock_db.add.call_count >= 1
            assert mock_db.commit.call_count >= 1
