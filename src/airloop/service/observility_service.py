from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4

from langfuse import Langfuse

from airloop.settings import LangfuseConfig


class ObservabilityService:
    def start_round_trace(
        self,
        *,
        conversation_id: str,
        round_id: int,
        user_message: str,
        agent_name: str,
        context: Dict[str, Any],
    ) -> str:
        raise NotImplementedError

    def log_round(self, *, trace_id: str, messages: Any, events: Any, next_agent: str | None, context: Dict[str, Any]) -> None:
        raise NotImplementedError

    def log_guardrail_trip(self, *, trace_id: str, reason: str) -> None:
        raise NotImplementedError

    def score(self, *, trace_id: str, name: str, value: float, comment: str | None = None) -> None:
        raise NotImplementedError


class NoopObservabilityService(ObservabilityService):
    def __init__(self) -> None:
        self.enabled = False

    def start_round_trace(
        self,
        *,
        conversation_id: str,
        round_id: int,
        user_message: str,
        agent_name: str,
        context: Dict[str, Any],
    ) -> str:
        return uuid4().hex

    def log_round(self, *, trace_id: str, messages: Any, events: Any, next_agent: str | None, context: Dict[str, Any]) -> None:
        return None

    def log_guardrail_trip(self, *, trace_id: str, reason: str) -> None:
        return None

    def score(self, *, trace_id: str, name: str, value: float, comment: str | None = None) -> None:
        return None


class LangfuseObservabilityService(ObservabilityService):
    def __init__(self, config: LangfuseConfig):
        self.config = config
        self.enabled = True
        self.client = Langfuse(
            public_key=config.public_key,
            secret_key=config.secret_key,
            host=config.host,
            release=config.release,
        )

    def start_round_trace(
        self,
        *,
        conversation_id: str,
        round_id: int,
        user_message: str,
        agent_name: str,
        context: Dict[str, Any],
    ) -> str:
        trace_id = uuid4().hex
        try:
            self.client.trace(
                id=trace_id,
                name="chat_round",
                input={"user_message": user_message},
                metadata={
                    "conversation_id": conversation_id,
                    "round_id": round_id,
                    "agent_name": agent_name,
                    "context": context,
                },
            )
        except Exception:
            return trace_id
        return trace_id

    def log_round(self, *, trace_id: str, messages: Any, events: Any, next_agent: str | None, context: Dict[str, Any]) -> None:
        try:
            trace = self.client.trace(id=trace_id)
            trace.event(
                name="agent_round",
                input={"messages": messages, "events": events, "next_agent": next_agent, "context": context},
            )
            trace.update(output={"messages": messages, "events": events}, metadata={"next_agent": next_agent, "context": context})
        except Exception:
            return None

    def log_guardrail_trip(self, *, trace_id: str, reason: str) -> None:
        try:
            trace = self.client.trace(id=trace_id)
            trace.event(name="guardrail_trip", input={"reason": reason})
            trace.score(name="guardrail_trip", value=0.0, comment=reason)
        except Exception:
            return None

    def score(self, *, trace_id: str, name: str, value: float, comment: str | None = None) -> None:
        try:
            trace = self.client.trace(id=trace_id)
            trace.score(name=name, value=value, comment=comment)
        except Exception:
            return None
