# LLM client tests
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from ..llm_client import LLMClient
from ..config import settings


class TestLLMClient:

    @pytest.fixture
    def client(self):
        return LLMClient()

    def test_endpoint_generation(self, client):
        # Test OpenAI endpoint
        client.provider = "openai"
        assert client._get_endpoint() == "https://api.openai.com/v1/chat/completions"

        # Test Azure endpoint
        client.provider = "azure"
        settings.azure_openai_endpoint = "https://test.openai.azure.com"
        settings.azure_openai_deployment = "test-deployment"
        endpoint = client._get_endpoint()
        assert "test.openai.azure.com" in endpoint
        assert "test-deployment" in endpoint

    def test_headers_generation(self, client):
        # Test OpenAI headers
        client.provider = "openai"
        headers = client._get_headers()
        assert "Authorization" in headers
        assert "Bearer" in headers["Authorization"]

        # Test Azure headers
        client.provider = "azure"
        headers = client._get_headers()
        assert "api-key" in headers

    def test_message_building(self, client):
        messages = [{"role": "user", "content": "test"}]

        # Without command
        result = client._build_messages(messages)
        assert len(result) == 1

        # With command
        result = client._build_messages(messages, "/explain")
        assert len(result) == 2
        assert result[0]["role"] == "system"

    @pytest.mark.asyncio
    async def test_generate_stream(self, client):
        with patch("httpx.AsyncClient.stream") as mock_stream:
            mock_response = AsyncMock()
            mock_response.aiter_lines.return_value = [
                'data: {"choices":[{"delta":{"content":"Hello"}}]}',
                'data: {"choices":[{"delta":{"content":" world"}}]}',
                "data: [DONE]",
            ]
            mock_stream.return_value.__aenter__.return_value = mock_response

            result = []
            async for chunk in client.generate_stream(
                [{"role": "user", "content": "Hi"}]
            ):
                result.append(chunk)

            assert result == ["Hello", " world"]

    @pytest.mark.asyncio
    async def test_generate_non_stream(self, client):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test response"}}]
            }
            mock_post.return_value = mock_response

            result = await client.generate([{"role": "user", "content": "Hi"}])
            assert result == "Test response"
