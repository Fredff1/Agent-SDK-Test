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
    description_override="Order in-flight food for the passenger. Requires a meal name.",
)
async def order_food(
    context: RunContextWrapper[AirlineAgentContext],
    meal: str,
) -> str:
    """
    Order a meal and update context with the selection.
    """
    if not meal:
        return "Please specify a meal to order."

    # Normalize and validate meal against available list if present.
    available = [m.lower() for m in (context.context.available_meals or [])]
    if available and meal.lower() not in available:
        return f"Meal '{meal}' is not available. Available meals: {', '.join(context.context.available_meals)}"

    context.context.meal_selection = meal
    return f"Order placed for: {meal}"

