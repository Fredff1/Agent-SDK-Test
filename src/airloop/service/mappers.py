from __future__ import annotations
import time
from uuid import uuid4
from typing import Any, Dict, List, Tuple

from agents import (
    ItemHelpers,
    MessageOutputItem,
    HandoffOutputItem,
    ToolCallItem,
    ToolCallOutputItem,
)

def extract_messages_events(result) -> tuple[list[dict], list[dict], str | None]:
    """
    return: (messages, events, next_agent_name)
    messages: [{"content": str, "agent": str}, ...]
    events:   [{"id":..., "type":..., "agent":..., "content":..., "metadata":..., "timestamp":...}, ...]
    """
    messages: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []
    next_agent_name: str | None = None

    for item in result.new_items:
        ts = time.time() * 1000

        if isinstance(item, MessageOutputItem):
            text = ItemHelpers.text_message_output(item)
            messages.append({"content": text, "agent": item.agent.name})
            events.append({"id": uuid4().hex, "type": "message", "agent": item.agent.name, "content": text, "timestamp": ts})

        elif isinstance(item, HandoffOutputItem):
            events.append({
                "id": uuid4().hex,
                "type": "handoff",
                "agent": item.source_agent.name,
                "content": f"{item.source_agent.name} -> {item.target_agent.name}",
                "metadata": {"source_agent": item.source_agent.name, "target_agent": item.target_agent.name},
                "timestamp": ts,
            })
            next_agent_name = item.target_agent.name

        elif isinstance(item, ToolCallItem):
            tool_name = getattr(item.raw_item, "name", "") or ""
            raw_args = getattr(item.raw_item, "arguments", None)
            events.append({
                "id": uuid4().hex,
                "type": "tool_call",
                "agent": item.agent.name,
                "content": tool_name,
                "metadata": {"arguments": raw_args},
                "timestamp": ts,
            })

        elif isinstance(item, ToolCallOutputItem):
            events.append({
                "id": uuid4().hex,
                "type": "tool_output",
                "agent": item.agent.name,
                "content": str(item.output),
                "metadata": {"tool_result": item.output},
                "timestamp": ts,
            })

    return messages, events, next_agent_name
