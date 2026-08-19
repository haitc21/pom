import json
from dataclasses import dataclass
from typing import Any

import httpx

from aic.config import Settings


class HolmesError(RuntimeError):
    pass


@dataclass(frozen=True)
class HolmesApproval:
    pending_calls: list[dict[str, Any]]
    conversation_history: list[dict[str, Any]]


@dataclass(frozen=True)
class HolmesResult:
    answer: str | None = None
    approval: HolmesApproval | None = None


class HolmesClient:
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.holmes_url.rstrip("/")
        self.timeout = settings.holmes_timeout_seconds
        self.max_response_bytes = settings.holmes_max_response_bytes
        self.api_key = settings.holmes_api_key.get_secret_value()

    def chat(
        self,
        prompt: str,
        model: str,
        *,
        conversation_history: list[dict[str, Any]] | None = None,
        tool_decisions: list[dict[str, Any]] | None = None,
    ) -> HolmesResult:
        payload: dict[str, Any] = {
            "ask": prompt,
            "model": model,
            "stream": True,
            "enable_tool_approval": True,
        }
        if conversation_history is not None:
            payload["conversation_history"] = conversation_history
        if tool_decisions is not None:
            payload["tool_decisions"] = tool_decisions
        try:
            with httpx.Client(timeout=self.timeout) as client:
                headers = {"X-API-Key": self.api_key} if self.api_key else {}
                with client.stream("POST", f"{self.base_url}/api/chat", json=payload, headers=headers) as response:
                    response.raise_for_status()
                    return self._parse_stream(response)
        except httpx.HTTPError as exc:
            raise HolmesError("HolmesGPT request failed") from exc

    def _parse_stream(self, response: httpx.Response) -> HolmesResult:
        total_bytes = 0
        answer_parts: list[str] = []
        for line in response.iter_lines():
            if not line or not line.startswith("data:"):
                continue
            raw = line.removeprefix("data:").strip()
            if raw == "[DONE]":
                break
            total_bytes += len(raw.encode())
            if total_bytes > self.max_response_bytes:
                raise HolmesError("HolmesGPT stream exceeded the configured size limit")
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            approval = self._approval_from_event(event)
            if approval is not None:
                return HolmesResult(approval=approval)
            text = self._answer_from_event(event)
            if text:
                answer_parts.append(text)
        answer = "".join(answer_parts).strip()
        if not answer:
            raise HolmesError("HolmesGPT stream ended without an answer or approval")
        return HolmesResult(answer=answer)

    @staticmethod
    def _approval_from_event(event: Any) -> HolmesApproval | None:
        if not isinstance(event, dict):
            return None
        pending = event.get("pending_approvals")
        if event.get("requires_approval") is not True or not isinstance(pending, list) or not pending:
            return None
        history = event.get("conversation_history")
        if not isinstance(history, list):
            raise HolmesError("HolmesGPT approval event omitted conversation_history")
        valid_calls = [item for item in pending if isinstance(item, dict) and item.get("tool_call_id")]
        if not valid_calls:
            raise HolmesError("HolmesGPT approval event contained no valid tool calls")
        return HolmesApproval(pending_calls=valid_calls, conversation_history=history)

    @staticmethod
    def _answer_from_event(event: Any) -> str | None:
        if isinstance(event, str):
            return event
        if not isinstance(event, dict):
            return None
        for key in ("answer", "response", "analysis", "result", "content"):
            value = event.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                nested = HolmesClient._answer_from_event(value)
                if nested:
                    return nested
        return None
