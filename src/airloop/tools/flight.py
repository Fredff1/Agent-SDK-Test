import string
import random

from agents import (
    Agent,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    function_tool,
    handoff,
    GuardrailFunctionOutput,
    input_guardrail,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from airloop.domain.context import AirlineAgentContext

@function_tool(
    name_override="flight_status_tool",
    description_override="Lookup status for a flight."
)
async def flight_status_tool(flight_number: str) -> str:
    """Lookup the status for a flight."""
    return f"Flight {flight_number} is on time and scheduled to depart at gate A10."


# Cancellation tool and agent
@function_tool(
    name_override="cancel_flight",
    description_override="Cancel a flight."
)
async def cancel_flight(
    context: RunContextWrapper[AirlineAgentContext]
) -> str:
    """Cancel the flight in the context."""
    fn = context.context.flight_number
    assert fn is not None, "Flight number is required"
    return f"Flight {fn} successfully cancelled"


@function_tool(
    name_override="baggage_tool",
    description_override="Lookup baggage allowance and fees."
)
async def baggage_tool(query: str) -> str:
    """Lookup baggage allowance and fees."""
    q = query.lower()
    if "fee" in q:
        return "Overweight bag fee is $75."
    if "allowance" in q:
        return "One carry-on and one checked bag (up to 50 lbs) are included."
    return "Please provide details about your baggage inquiry."