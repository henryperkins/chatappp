# Unified LLM client for OpenAI and Azure OpenAI
import os
import httpx
import json
import asyncio
from typing import AsyncGenerator, Dict, List, Optional, Any
from .config import settings
import backoff


class LLMClient:
    def __init__(self):
        self.provider = settings.openai_provider
        self.model = settings.openai_model
        self.timeout = httpx.Timeout(30.0, read=120.0)

    def _get_endpoint(self) -> str:
        if self.provider == "azure":
            base = settings.azure_openai_endpoint.rstrip("/")
            deployment = settings.azure_openai_deployment
            version = settings.azure_openai_api_version
            return f"{base}/openai/deployments/{deployment}/chat/completions?api-version={version}"
        return "https://api.openai.com/v1/chat/completions"

    def _get_headers(self) -> Dict[str, str]:
        """
        Build the correct auth header for the selected provider.
        • OpenAI → standard bearer token
        • Azure OpenAI → `api-key` header (prefer AZURE_OPENAI_API_KEY,
          fall back to OPENAI_API_KEY for backward-compatibility)
        """
        if self.provider == "azure":
            api_key = settings.azure_openai_api_key or settings.openai_api_key
            if not api_key:
                raise RuntimeError(
                    "Azure provider selected but AZURE_OPENAI_API_KEY / OPENAI_API_KEY is not set"
                )
            return {"api-key": api_key}

        return {"Authorization": f"Bearer {settings.openai_api_key}"}

    def _build_messages(
        self, messages: List[Dict[str, str]], command: Optional[str] = None
    ) -> List[Dict[str, str]]:
        system_prompts = {
            "/explain": "You are a helpful coding assistant. Explain the provided code clearly and concisely.",
            "/refactor": "You are an expert code refactorer. Improve the provided code for readability, performance, and maintainability.",
            "/tests": "You are a test-driven development expert. Generate comprehensive unit tests for the provided code.",
            "/summarize": "You are a concise technical writer. Summarize the key points of our conversation.",
        }

        result = []
        if command and command in system_prompts:
            result.append({"role": "system", "content": system_prompts[command]})

        result.extend(messages)
        return result

    @backoff.on_exception(
        backoff.expo, (httpx.HTTPStatusError, httpx.RequestError), max_time=60
    )
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        command: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:

        body = {
            "messages": self._build_messages(messages, command),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if self.provider == "openai":
            body["model"] = self.model

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST", self._get_endpoint(), headers=self._get_headers(), json=body
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            if chunk.get("choices") and chunk["choices"][0].get(
                                "delta", {}
                            ).get("content"):
                                yield chunk["choices"][0]["delta"]["content"]
                        except json.JSONDecodeError:
                            continue

    async def generate(
        self,
        messages: List[Dict[str, str]],
        command: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:

        body = {
            "messages": self._build_messages(messages, command),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        if self.provider == "openai":
            body["model"] = self.model

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self._get_endpoint(), headers=self._get_headers(), json=body
            )
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]
