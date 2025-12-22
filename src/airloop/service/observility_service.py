from typing import Any

class ObservabilityService:
    def start_round_trace(self, *, conversation_id: str, round_id: int, user_message: str, agent_name: str, context: Dict[str, Any]) -> str:
        ...

    def log_round(self, *, trace_id: str, messages: Any, events: Any, next_agent: str | None, context: Dict[str, Any]) -> None:
        ...

    def log_guardrail_trip(self, *, trace_id: str, reason: str) -> None:
        ...

    def score(self, *, trace_id: str, name: str, value: float, comment: str | None = None) -> None:
        ...
