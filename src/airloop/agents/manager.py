from typing import Dict, List, Optional
from dataclasses import dataclass

from openai import AsyncOpenAI
from pydantic import BaseModel
from agents import (
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
    Agent,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    handoff,
    GuardrailFunctionOutput,
    input_guardrail,
)

from airloop.agents.role import AgentRole
from airloop.agents.guard import GuardrailManager, get_jailbreak_guardrail_agent, get_relevance_guardrail_agent, RelevanceOutput, JailbreakOutput
from airloop.agents.faq import get_faq_agent
from airloop.agents.flight import get_flight_status_agent, get_flight_cancel_agent, on_cancellation_handoff
from airloop.agents.seat_booking import get_seat_booking_agent, on_seat_booking_handoff
from airloop.agents.triage import get_triage_agent
from airloop.agents.food import get_food_agent
from airloop.provider.qwen import QwenModelProvider, build_qwen3_run_config
from airloop.settings import UserConfig
from pydantic import BaseModel

HANDOFF_ROLES = [ 
    AgentRole.FLIGHT_CANCEL,
    AgentRole.FLIGHT_STATUS,
    AgentRole.SEAT_BOOKING,
    AgentRole.FAQ,
    AgentRole.FOOD,
]

HANDOFF_HANDLERS = {
    AgentRole.FLIGHT_CANCEL: on_cancellation_handoff,
    AgentRole.SEAT_BOOKING: on_seat_booking_handoff,
}

@dataclass
class _AgentStore:
    agent: Agent
    role: AgentRole
    
    @property
    def name(self):
        return self.agent.name
    
    @property
    def guardrail_names(self):
        names = []
        for gd in self.agent.input_guardrails:
            names.append(gd.get_name())
        return names
            
    @property
    def handoff_names(self):
        names = []
        for hf in self.agent.handoffs:
            if isinstance(hf, Agent):
                names.append(hf.name)
            else:
                names.append(hf.agent_name)
        return names
    
    @property
    def tool_names(self):
        names = []
        for tool in self.agent.tools:
            names.append(getattr(tool,"name",""))
        return names
            
    def as_dict(self):
        
        return {
            "name": self.name,
            "description": self.agent.handoff_description,
            "handoffs": self.handoff_names,
            "tools":self.tool_names,
            "input_guardrails": self.guardrail_names
        }

class AgentManager:
    def __init__(
        self,
        config: UserConfig
    ):
        set_tracing_disabled(True)
        self.config = config
        self.agents: Dict[AgentRole, Agent] = dict()
        self._storage: Dict[str, _AgentStore] = dict()
        self.client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=config.api_key
        )
        self.model = OpenAIChatCompletionsModel(model=config.model_name, openai_client=self.client)
        self.run_config = build_qwen3_run_config(QwenModelProvider())
        self._init_agents()

        
    def get_agent_by_name(self, name: str):
        st = self._storage.get(name, None)
        if not st:
            raise ValueError(f"Agent of name {name} not exist")
        return st.agent
    
    def get_agent_by_role(self, role: AgentRole):
        ag = self.agents.get(role, None)
        if not ag:
            raise ValueError(f"Agent of role {role} not exist")
        return ag
    
    def add_agent(self, role: AgentRole, ag: Agent):
        self.agents[role] = ag
        self._storage[ag.name]=_AgentStore(
            agent=ag,
            role=role
        )
        
        
    def _init_agents(self):
        self.add_agent(AgentRole.GUARD_JAILBREAK, get_jailbreak_guardrail_agent(self.model))
        self.add_agent(AgentRole.GUARD_RELEVANCE, get_relevance_guardrail_agent(self.model))
        
        self.guardrail_manager = GuardrailManager(self.agents, run_config=self.run_config)
        self.add_agent(AgentRole.SEAT_BOOKING, get_seat_booking_agent(self.model, self.guardrail_manager))
        self.add_agent(AgentRole.FLIGHT_STATUS, get_flight_status_agent(self.model, self.guardrail_manager))
        self.add_agent(AgentRole.FLIGHT_CANCEL, get_flight_cancel_agent(self.model, self.guardrail_manager))
        self.add_agent(AgentRole.FAQ, get_faq_agent(self.model, self.guardrail_manager))
        self.add_agent(AgentRole.FOOD, get_food_agent(self.model, self.guardrail_manager))

        handoffs = self._build_handoff()
        self.add_agent(AgentRole.TRIAGE, get_triage_agent(model=self.model, guardrail_mgr=self.guardrail_manager, handoffs=handoffs))
        for role in HANDOFF_ROLES:
            self.get_agent_by_role(role).handoffs.append(self.agents[AgentRole.TRIAGE])
    
    
    def _build_handoff(self):
        handoffs = []
        for role in HANDOFF_ROLES:
            ag = self.agents[role]
            if role in HANDOFF_HANDLERS:
                handoffs.append(handoff(ag, on_handoff = HANDOFF_HANDLERS[role]))
            else:
                handoffs.append(handoff(ag))
        return handoffs
    
    def list_agents(self, filter: Optional[List[AgentRole]] = None):
        if filter:
            candidates = [st.as_dict() for st in self._storage.values() if st.role in filter]
        else:
            candidates = [st.as_dict() for st in self._storage.values()]
        return candidates
    
   

            
        

        
        
    
