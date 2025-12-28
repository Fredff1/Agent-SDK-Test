from __future__ import annotations
from uuid import uuid4
from typing import Any, Dict, Optional

from agents import Runner, InputGuardrailTripwireTriggered

from airloop.agents.role import AgentRole
from airloop.domain.schema import ConversationStore, ConversationState
from airloop.domain.context import create_initial_context
from airloop.service.mappers import extract_messages_events
from airloop.agents.manager import AgentManager
from airloop.service.observility_service import NoopObservabilityService, ObservabilityService
import logging


ROLES_TO_SHOW = [
    AgentRole.FLIGHT_CANCEL,
    AgentRole.FLIGHT_STATUS,
    AgentRole.FAQ,
    AgentRole.SEAT_BOOKING,
    AgentRole.TRIAGE,
    AgentRole.FOOD
]

GUARD_RAIL_ROLES=[
    AgentRole.GUARD_RELEVANCE,
    AgentRole.GUARD_JAILBREAK
]




class ChatService:
    def __init__(self, agent_mgr: AgentManager, store: ConversationStore, obs_service: ObservabilityService | None = None):
        self.agent_mgr = agent_mgr
        self.store = store
        self.obs_service = obs_service or NoopObservabilityService()

    def _init_state(self) -> tuple[str, ConversationState]:
        cid = uuid4().hex
        triage = self.agent_mgr.get_agent_by_role(AgentRole.TRIAGE)
        state = ConversationState(
            state_id=cid,
            input_items=[{"role":"user","content":"A customer starts a new session, please provide your assistance."}],
            current_agent_name=triage.name,
            context=create_initial_context(),  
        )
        state.bound_context()
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
        return await self._chat_with_state(state, message, persist=True)

    async def chat_with_state(self, state: ConversationState, message: str, persist: bool = False) -> Dict[str, Any]:
        """
        Allow running chat flow against a provided ConversationState (for offline eval).
        When persist=False, state is not saved back to the store.
        """
        return await self._chat_with_state(state, message, persist=persist)
    
    async def _chat_with_state(self, state: ConversationState, message: str, persist: bool = True) -> Dict[str, Any]:
        cid = state.state_id
        agent = self.agent_mgr.get_agent_by_name(state.current_agent_name)
        state.input_items.append({"role": "user", "content": message})
        round_id = state.round_counter
        with self.obs_service.start_round_trace(
            conversation_id=cid,
            round_id=round_id,
            input_messages=state.input_items,
            agent_name=agent.name,
            context=state.context,
        ) as trace_id:

            try:
                result = await Runner.run(
                    agent,
                    state.input_items,
                    context=state.context,
                    run_config=self.agent_mgr.run_config,
                )
            except InputGuardrailTripwireTriggered:
                refusal = "Sorry, I can only answer questions related to airline travel."
                guardrail_checks = self.agent_mgr.guardrail_manager.pop_guardrail_checks()
                state.update_round(
                    agent_name=state.current_agent_name,
                    trace_id=trace_id,
                    input_items=state.input_items,
                    events=[],
                    messages=[{"role": "assistant", "content": refusal}]
                )
                self.obs_service.log_guardrail_trip(trace_id=trace_id, reason="Input relevance guardrail triggered")
                state.input_items.append({"role": "assistant", "content": refusal})
                state.finish_round()
                if persist:
                    self.store.save(cid, state)
                return {
                    "conversation_id": cid,
                    "current_agent": agent.name,
                    "messages": [{"content": refusal, "agent": agent.name}],
                    "events": [],
                    "context": state.context,
                    "agents": self.agent_mgr.list_agents(filter=ROLES_TO_SHOW),
                    "guardrails": guardrail_checks,
                    "trace_id": trace_id,
                }
            except Exception as exc:
                logging.exception("ChatService run failed")
                error_msg = "Sorry, something went wrong on our side. Please try again."
                guardrail_checks = self.agent_mgr.guardrail_manager.pop_guardrail_checks()
                state.update_round(
                    agent_name=state.current_agent_name,
                    trace_id=trace_id,
                    input_items=state.input_items,
                    events=[],
                    messages=[{"role": "assistant", "content": error_msg}],
                )
                state.input_items.append({"role": "assistant", "content": error_msg})
                state.finish_round()
                if persist:
                    self.store.save(cid, state)
                return {
                    "conversation_id": cid,
                    "current_agent": state.current_agent_name,
                    "messages": [{"content": error_msg, "agent": agent.name}],
                    "events": [],
                    "context": state.context,
                    "agents": self.agent_mgr.list_agents(filter=ROLES_TO_SHOW),
                    "guardrails": guardrail_checks,
                    "trace_id": trace_id,
                }

            messages, events, next_agent_name = extract_messages_events(result)
            guardrail_checks = self.agent_mgr.guardrail_manager.pop_guardrail_checks()
            
            self.obs_service.log_round(
                conversation_id=cid,
                trace_id=trace_id,
                messages=messages,
                events=events,
                next_agent=next_agent_name,
                context=state.context,
                input_content=state.input_items,
            )
            
            state.update_round(
                agent_name=state.current_agent_name, 
                input_items=state.input_items,
                trace_id=trace_id,
                events=events,
                messages=messages,
            )
            state.input_items = result.to_input_list()
            
            state.current_agent_name = next_agent_name or state.current_agent_name
            # print(state.input_items)
            state.finish_round()
            if persist:
                self.store.save(cid, state)
        
        return {
            "conversation_id": cid,
            "current_agent": state.current_agent_name,
            "messages": messages,
            "events": events,
            "context": state.context,
            "agents": self.agent_mgr.list_agents(filter=ROLES_TO_SHOW),
            "guardrails": guardrail_checks,
            "trace_id": trace_id,
        }
