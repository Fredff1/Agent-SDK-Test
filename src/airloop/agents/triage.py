from pydantic import BaseModel
from typing import Dict, List, Any

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


def get_triage_agent(
    model,
    guardrail_mgr: GuardrailManager,
    handoffs: List[Agent[Any]]
):

    triage_agent = Agent[AirlineAgentContext](
        name="Triage Agent",
        #model="gpt-4.1",
        model=model,  ##changed to qwen model， useless when only one model for all agents
        handoff_description="A triage agent that can delegate a customer's request to the appropriate agent.",
        instructions=(
            f"{RECOMMENDED_PROMPT_PREFIX} "
            "You are a helpful triaging agent. You can use your tools to delegate questions to other appropriate agents."
        ),
        # handoffs=[
        #     flight_status_agent,
        #     handoff(agent=cancellation_agent, on_handoff=on_cancellation_handoff),
        #     faq_agent,
        #     handoff(agent=seat_booking_agent, on_handoff=on_seat_booking_handoff),
        # ],
        handoffs=handoffs,
        input_guardrails=[guardrail_mgr.relevance_guardrail, guardrail_mgr.jailbreak_guardrail],
    )
    return triage_agent