from typing import Any, List

from agents import Agent, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from airloop.agents.guard import GuardrailManager
from airloop.agents.flight import flight_status_instructions, cancellation_instructions, on_cancellation_handoff
from airloop.agents.seat_booking import seat_booking_instructions, on_seat_booking_handoff
from airloop.domain.context import AirlineAgentContext
from airloop.tools.flight import flight_status_tool, cancel_flight
from airloop.tools.seat import update_seat, display_seat_map
from airloop.tools.food import order_food
from airloop.tools.faq import faq_lookup_tool


def get_legacy_flight_status_agent(model, guardrail_mgr: GuardrailManager):
    return Agent[AirlineAgentContext](
        name="Flight Status Agent",
        model=model,
        handoff_description="An agent to provide flight status information.",
        instructions=flight_status_instructions,
        tools=[flight_status_tool],
        input_guardrails=[guardrail_mgr.jailbreak_guardrail],
    )


def get_legacy_flight_cancel_agent(model, guardrail_mgr: GuardrailManager):
    return Agent[AirlineAgentContext](
        name="Cancellation Agent",
        model=model,
        handoff_description="An agent to cancel flights.",
        instructions=cancellation_instructions,
        tools=[cancel_flight],
        input_guardrails=[guardrail_mgr.jailbreak_guardrail],
    )


def get_legacy_seat_booking_agent(model, guardrail_mgr: GuardrailManager):
    return Agent[AirlineAgentContext](
        name="Seat Booking Agent",
        model=model,
        handoff_description="A helpful agent that can help book or update a seat on a flight.",
        instructions=seat_booking_instructions,
        tools=[update_seat, display_seat_map],
        input_guardrails=[guardrail_mgr.jailbreak_guardrail],
    )


def get_legacy_food_agent(model, guardrail_mgr: GuardrailManager):
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

    return Agent[AirlineAgentContext](
        name="Food Agent",
        model=model,
        handoff_description="A helpful agent that can answer questions about the food supplies and order foods.",
        instructions=food_instructions,
        tools=[order_food],
        input_guardrails=[guardrail_mgr.jailbreak_guardrail],
    )


def get_legacy_faq_agent(model, guardrail_mgr: GuardrailManager):
    return Agent[AirlineAgentContext](
        name="FAQ Agent",
        model=model,
        handoff_description="A helpful agent that can answer questions about the airline.",
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        You are an FAQ agent. If you are speaking to a customer, you probably were transferred to from the triage agent.
        Use the following routine to support the customer.
        1. Identify the last question asked by the customer.
        2. Use the faq lookup tool to get the answer. Do not rely on your own knowledge.
        3. Respond to the customer with the answer""",
        tools=[faq_lookup_tool],
        input_guardrails=[guardrail_mgr.relevance_guardrail, guardrail_mgr.jailbreak_guardrail],
    )


def get_legacy_triage_agent(model, guardrail_mgr: GuardrailManager, handoffs: List[Agent[Any]]):
    return Agent[AirlineAgentContext](
        name="Triage Agent",
        model=model,
        handoff_description="A triage agent that can delegate a customer's request to the appropriate agent.",
        instructions=(
            f"{RECOMMENDED_PROMPT_PREFIX} "
            "You are a helpful triaging agent. You can use your tools to delegate questions to other appropriate agents."
        ),
        handoffs=handoffs,
        input_guardrails=[guardrail_mgr.relevance_guardrail, guardrail_mgr.jailbreak_guardrail],
    )
