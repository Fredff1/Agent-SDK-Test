from typing import Dict, List, Optional, Any

from agents import Agent, handoff

from airloop.agents.guard import GuardrailManager, get_jailbreak_guardrail_agent, get_relevance_guardrail_agent
from airloop.agents.legacy_agents import (
    get_legacy_faq_agent,
    get_legacy_flight_cancel_agent,
    get_legacy_flight_status_agent,
    get_legacy_food_agent,
    get_legacy_seat_booking_agent,
    get_legacy_triage_agent,
)
from airloop.agents.flight import on_cancellation_handoff
from airloop.agents.seat_booking import on_seat_booking_handoff
from airloop.agents.role import AgentRole


class MockAgentManager:
    def __init__(self, model, run_config):
        self.model = model
        self.run_config = run_config
        self.agents: Dict[AgentRole, Agent] = {}
        self.guardrail_manager: Optional[GuardrailManager] = None
        self._storage: Dict[str, Agent] = {}
        self._init_agents()

    def _register(self, role: AgentRole, agent: Agent):
        self.agents[role] = agent
        self._storage[agent.name] = agent

    def _init_agents(self):
        self._register(AgentRole.GUARD_JAILBREAK, get_jailbreak_guardrail_agent(self.model))
        self._register(AgentRole.GUARD_RELEVANCE, get_relevance_guardrail_agent(self.model))
        self.guardrail_manager = GuardrailManager(self.agents, run_config=self.run_config)

        self._register(AgentRole.SEAT_BOOKING, get_legacy_seat_booking_agent(self.model, self.guardrail_manager))
        self._register(AgentRole.FLIGHT_STATUS, get_legacy_flight_status_agent(self.model, self.guardrail_manager))
        self._register(AgentRole.FLIGHT_CANCEL, get_legacy_flight_cancel_agent(self.model, self.guardrail_manager))
        self._register(AgentRole.FAQ, get_legacy_faq_agent(self.model, self.guardrail_manager))
        self._register(AgentRole.FOOD, get_legacy_food_agent(self.model, self.guardrail_manager))

        handoffs = self._build_handoffs()
        self._register(AgentRole.TRIAGE, get_legacy_triage_agent(self.model, self.guardrail_manager, handoffs=handoffs))
        for role in [
            AgentRole.FLIGHT_CANCEL,
            AgentRole.FLIGHT_STATUS,
            AgentRole.SEAT_BOOKING,
            AgentRole.FAQ,
            AgentRole.FOOD,
        ]:
            self.get_agent_by_role(role).handoffs.append(self.agents[AgentRole.TRIAGE])

    def _build_handoffs(self):
        handoffs = []
        handlers = {
            AgentRole.FLIGHT_CANCEL: on_cancellation_handoff,
            AgentRole.SEAT_BOOKING: on_seat_booking_handoff,
        }
        for role in [
            AgentRole.FLIGHT_CANCEL,
            AgentRole.FLIGHT_STATUS,
            AgentRole.SEAT_BOOKING,
            AgentRole.FAQ,
            AgentRole.FOOD,
        ]:
            ag = self.agents[role]
            if role in handlers:
                handoffs.append(handoff(ag, on_handoff=handlers[role]))
            else:
                handoffs.append(handoff(ag))
        return handoffs

    def get_agent_by_name(self, name: str):
        agent = self._storage.get(name)
        if not agent:
            raise ValueError(f"Agent of name {name} not exist")
        return agent

    def get_agent_by_role(self, role: AgentRole):
        ag = self.agents.get(role)
        if not ag:
            raise ValueError(f"Agent of role {role} not exist")
        return ag

    def list_agents(self, filter: Optional[List[AgentRole]] = None):
        agents = list(self.agents.values())
        if filter:
            agents = [ag for role, ag in self.agents.items() if role in filter]
        return [{"name": ag.name, "description": getattr(ag, "handoff_description", ""), "handoffs": [], "tools": [], "input_guardrails": []} for ag in agents]
