from typing import Dict, List, Any

from pydantic import BaseModel
from agents import Agent

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from airloop.tools.food import order_food
from airloop.agents.guard import GuardrailManager
from airloop.domain.context import AirlineAgentContext


def get_faq_agent(
    model,
    guardrail_mgr: GuardrailManager,
):  
    food_agent = Agent[AirlineAgentContext](
        name="Food Agent",
        #model="gpt-4.1",
        model=model,  #changed to qwen model， useless when only one model for all agents
        
        handoff_description="A helpful agent that can answer questions about the airline.",
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        You are an food ordering agent. If you are speaking to a customer, you probably were transferred to from the triage agent.
        Use the following routine to support the customer.
        1.Provide the food list to customer, available food includes chicken and beef set
        2.If the customer orders any food, call corresponding tools to handle the task.
        3.Inform the customer of the order results.
        """,
        tools=[order_food],
        input_guardrails=[guardrail_mgr.relevance_guardrail, guardrail_mgr.jailbreak_guardrail],
    )
    return food_agent
