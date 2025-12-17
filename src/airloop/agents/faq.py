from pydantic import BaseModel
from typing import Dict, List

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
from airloop.tools.faq import faq_lookup_tool


def get_faq_agent(
    model,
    guardrail_mgr: GuardrailManager,
):  

    faq_agent = Agent[AirlineAgentContext](
        name="FAQ Agent",
        #model="gpt-4.1",
        model=model,  #changed to qwen model， useless when only one model for all agents
        
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
    return faq_agent