from __future__ import annotations
from uuid import uuid4
from typing import Any, Dict, Optional

from agents import Runner, InputGuardrailTripwireTriggered

from airloop.agents.role import AgentRole
from airloop.domain.schema import ConversationStore, ConversationState
from airloop.domain.context import create_initial_context
from airloop.service.mappers import extract_messages_events
from airloop.agents.manager import AgentManager


ROLES_TO_SHOW = [
    AgentRole.FLIGHT_CANCEL,
    AgentRole.FLIGHT_CANCEL,
    AgentRole.FAQ,
    AgentRole.FLIGHT_STATUS,
    AgentRole.FLIGHT_STATUS,
]




class ChatService:
    def __init__(self, agent_mgr: AgentManager, store: ConversationStore):
        self.agent_mgr = agent_mgr
        self.store = store

    def _init_state(self) -> tuple[str, ConversationState]:
        cid = uuid4().hex
        triage = self.agent_mgr.get_agent_by_role(AgentRole.TRIAGE)
        state = ConversationState(
            input_items=[],
            current_agent_name=triage.name,
            context=create_initial_context(),  # TODO: 你有 ctx 的话在这里 model_dump
        )
        self.store.save(cid, state)
        return cid, state

    def _load_state(self, conversation_id: Optional[str]) -> tuple[str, ConversationState]:
        if not conversation_id:
            return self._init_state()
        st = self.store.get(conversation_id)
        if st is None:
            return self._init_state()
        return conversation_id, st

    async def chat(self, conversation_id: Optional[str], message: str) -> Dict[str, Any]:
        cid, state = self._load_state(conversation_id)

        agent = self.agent_mgr.get_agent_by_name(state.current_agent_name)
        state.input_items.append({"role": "user", "content": message})

        try:
            result = await Runner.run(
                agent,
                state.input_items,
                context=state.context,
                run_config=self.agent_mgr.run_config,
            )
        except InputGuardrailTripwireTriggered:
            refusal = "Sorry, I can only answer questions related to airline travel."
            state.input_items.append({"role": "assistant", "content": refusal})
            self.store.save(cid, state)
            return {
                "conversation_id": cid,
                "current_agent": agent.name,
                "messages": [{"content": refusal, "agent": agent.name}],
                "events": [],
                "context": state.context,
                "agents": self.agent_mgr.list_agents(filter=ROLES_TO_SHOW),
                "guardrails": [],
                "trace_id": uuid4().hex,
            }

        messages, events, next_agent_name = extract_messages_events(result)

        state.input_items = result.to_input_list()
        state.current_agent_name = next_agent_name or state.current_agent_name

        self.store.save(cid, state)

        return {
            "conversation_id": cid,
            "current_agent": state.current_agent_name,
            "messages": messages,
            "events": events,
            "context": state.context,
            "agents": self.agent_mgr.list_agents(filter=ROLES_TO_SHOW),
            "guardrails": [],
            "trace_id": uuid4().hex,
        }
