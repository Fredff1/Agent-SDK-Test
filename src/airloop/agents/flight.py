from pydantic import BaseModel
from typing import Dict, List
import random
import string

from pydantic import BaseModel
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

from airloop.agents.role import AgentRole
from airloop.agents.guard import GuardrailManager
from airloop.domain.context import AirlineAgentContext
from airloop.tools.flight import flight_status_tool, cancel_flight


def flight_status_instructions(
    run_context: RunContextWrapper[AirlineAgentContext], agent: Agent[AirlineAgentContext]
) -> str:
    ctx = run_context.context
    confirmation = ctx.confirmation_number or "[unknown]"
    flight = ctx.flight_number or "[unknown]"
    return (
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are a Flight Status Agent. Use the following routine to support the customer:\n"
        f"1. The customer's confirmation number is {confirmation} and flight number is {flight}.\n"
        "   If either is not available, ask the customer for the missing information. If you have both, confirm with the customer that these are correct.\n"
        "2. Use the flight_status_tool to report the status of the flight.\n"
        "If the customer asks a question that is not related to flight status, transfer back to the triage agent."
    )
    
def cancellation_instructions(
    run_context: RunContextWrapper[AirlineAgentContext], agent: Agent[AirlineAgentContext]
) -> str:
    ctx = run_context.context
    confirmation = ctx.confirmation_number or "[unknown]"
    flight = ctx.flight_number or "[unknown]"
    return (
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are a Cancellation Agent. Use the following routine to support the customer:\n"
        f"1. The customer's confirmation number is {confirmation} and flight number is {flight}.\n"
        "   If either is not available, ask the customer for the missing information. If you have both, confirm with the customer that these are correct.\n"
        "2. If the customer confirms, use the cancel_flight tool to cancel their flight.\n"
        "If the customer asks anything else, transfer back to the triage agent."
    )
    
async def on_cancellation_handoff(
    context: RunContextWrapper[AirlineAgentContext]
) -> None:
    """Ensure context has a confirmation and flight number when handing off to cancellation."""
    if context.context.confirmation_number is None:
        context.context.confirmation_number = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
    if context.context.flight_number is None:
        context.context.flight_number = f"FLT-{random.randint(100, 999)}"




    
def get_flight_status_agent(
    model,
    guardrail_mgr: GuardrailManager,
):

    flight_status_agent = Agent[AirlineAgentContext](
        name="Flight Status Agent",
        #model="gpt-4.1",
        model=model,  #changed to qwen model, useless when only one model for all agents
        
        handoff_description="An agent to provide flight status information.",
        instructions=flight_status_instructions,
        tools=[flight_status_tool],
        input_guardrails=[guardrail_mgr.jailbreak_guardrail],
    )
    return flight_status_agent

def get_flight_cancel_agent(
    model,
    guardrail_mgr: GuardrailManager,
):
    cancellation_agent = Agent[AirlineAgentContext](
        name="Cancellation Agent",
        #model="gpt-4.1",
        model=model,  ##changed to qwen model， useless when only one model for all agents
        
        handoff_description="An agent to cancel flights.",
        instructions=cancellation_instructions,
        tools=[cancel_flight],
        input_guardrails=[guardrail_mgr.jailbreak_guardrail],
    )
    return cancellation_agent
