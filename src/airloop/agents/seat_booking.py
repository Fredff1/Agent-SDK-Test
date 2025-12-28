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
from airloop.tools.seat import update_seat, display_seat_map




def seat_booking_instructions(
    run_context: RunContextWrapper[AirlineAgentContext], agent: Agent[AirlineAgentContext]
) -> str:
    ctx = run_context.context
    confirmation = ctx.confirmation_number or "[unknown]"
    return (
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are a seat booking agent. If you are speaking to a customer, you probably were transferred to from the triage agent.\n"
        "Use the following routine to support the customer.\n"
        f"1. The customer's confirmation number is {confirmation}."+
        "If this is not available, ask the customer for their confirmation number. If you have it, confirm that is the confirmation number they are referencing.\n"
        "2. Ask the customer what their desired seat number is. You can also use the display_seat_map tool to show them an interactive seat map where they can click to select their preferred seat.\n"
        "3. Use the update seat tool to update the seat on the flight.\n"
        "If the customer asks a question that is not related to the routine, transfer back to the triage agent."
    )
    
async def on_seat_booking_handoff(context: RunContextWrapper[AirlineAgentContext]) -> None:
    #=======================================================================================
    # Set flight and confirmation numbers for demo purposes
    # In production, these should be set from real or simulated user data
    #======================================================================================

    """Set a random flight number when handed off to the seat booking agent."""
    context.context.flight_number = f"FLT-{random.randint(100, 999)}"
    context.context.confirmation_number = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
def get_seat_booking_agent(
    model,
    guardrail_mgr: GuardrailManager,
):
    seat_booking_agent = Agent[AirlineAgentContext](
        name="Seat Booking Agent",
        #model="gpt-4.1",
        model=model,  #changed to qwen model, useless when only one model for all agents
        
        handoff_description="A helpful agent that can help book or update a seat on a flight.",
        instructions=seat_booking_instructions,
        tools=[update_seat, display_seat_map],
        input_guardrails=[guardrail_mgr.jailbreak_guardrail],
    )
    return seat_booking_agent