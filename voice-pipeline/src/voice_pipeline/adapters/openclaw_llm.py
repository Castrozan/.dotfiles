import asyncio
import logging
from collections.abc import AsyncIterator

import httpx
from httpx_sse import aconnect_sse

logger = logging.getLogger(__name__)


class OpenClawCompletion:
    def __init__(
        self,
        gateway_url: str,
        token: str,
        model: str = "anthropic/claude-sonnet-4-5",
    ) -> None:
        self._gateway_url = gateway_url.rstrip("/")
        self._token = token
        self._model = model
        self._client: httpx.AsyncClient | None = None
        self._cancel_event = asyncio.Event()

    async def stream(
        self,
        messages: list[dict[str, str]],
        agent: str,
    ) -> AsyncIterator[str]:
        self._cancel_event.clear()

        self._client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}",
            "x-clawdbot-agent-id": agent,
        }

        payload = {
            "model": self._model,
            "stream": True,
            "user": f"voice-{agent}",
            "messages": messages,
        }

        try:
            async with aconnect_sse(
                self._client,
                "POST",
                f"{self._gateway_url}/v1/chat/completions",
                json=payload,
                headers=headers,
            ) as event_source:
                async for sse in event_source.aiter_sse():
                    if self._cancel_event.is_set():
                        break

                    if sse.data == "[DONE]":
                        break

                    try:
                        import json
                        data = json.loads(sse.data)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, IndexError, KeyError):
                        continue
        except httpx.HTTPStatusError as exc:
            logger.error("Gateway HTTP error: %s", exc.response.status_code)
        except Exception:
            if not self._cancel_event.is_set():
                logger.exception("Gateway streaming error")
        finally:
            await self._client.aclose()
            self._client = None

    async def cancel(self) -> None:
        self._cancel_event.set()
        if self._client:
            await self._client.aclose()
            self._client = None
