from typing import Dict, List, Any

from pydantic import BaseModel
from agents import Agent, RunContextWrapper

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from airloop.tools.manager import ToolManager
from airloop.agents.guard import GuardrailManager
from airloop.domain.context import AirlineAgentContext


def get_food_agent(
    model,
    guardrail_mgr: GuardrailManager,
    tool_mgr: ToolManager,
):  
    def food_instructions(run_context: RunContextWrapper[AirlineAgentContext], agent: Agent[AirlineAgentContext]) -> str:
        meals = run_context.context.available_meals or ["Chicken set", "Beef set", "Vegetarian set"]
        pref = run_context.context.meal_preference or "[not provided]"
        return (
            f"{RECOMMENDED_PROMPT_PREFIX}\n"
            "You are a food ordering agent. If you are speaking to a customer, you were likely transferred from the triage agent.\n"
            f"Current dietary preference: {pref}.\n"
            f"Available meals: {', '.join(meals)}.\n"
            "Routine:\n"
            "1) Ask for dietary preference if unknown and consider it.\n"
            "2) Present available meals. If the customer orders, call the order_food tool with the chosen meal.\n"
            "3) Confirm the order and update context.meal_selection.\n"
            "If the request is not food-related, hand off back to triage."
        )

    food_agent = Agent[AirlineAgentContext](
        name="Food Agent",
        model=model, 
        handoff_description="A helpful agent that can answer questions about the food supplies and order foods.",
        instructions=food_instructions,
        tools=[tool_mgr.order_food],
        input_guardrails=[guardrail_mgr.jailbreak_guardrail],
    )
    return food_agent
