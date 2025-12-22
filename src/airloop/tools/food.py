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


# TODO Implementation
@function_tool(
    name_override="order_food",
    description_override="Order food."
)
async def order_food(
    context: RunContextWrapper[AirlineAgentContext]
) -> str:
    """Cancel the flight in the context."""
    return "Food is ordered"


