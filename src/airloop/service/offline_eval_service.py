from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Dict, Optional

from pydantic import BaseModel
from agents import Runner

from airloop.agents.manager import AgentManager
from airloop.agents.eval_agent import build_eval_agent, EvalScores
from airloop.agents.role import AgentRole
from airloop.domain.schema import ConversationState
from airloop.domain.context import AirlineAgentContext, create_initial_context
from airloop.service.chat_service import ChatService
from airloop.service.observility_service import ObservabilityService
from airloop.settings import AppConfig
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel


@dataclass
class EvalCase:
    name: str
    user_message: str
    expected: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, str]]] = None


class OfflineEvalService:
    """
    Run offline evaluations:
      - Call existing chat service to get assistant reply.
      - Use a dedicated LLM judge (eval agent) to score multi-dimension JSON.
      - Push each dimension as a Langfuse score on a new trace.
    """

    def __init__(
        self,
        chat_service: ChatService,
        agent_mgr: AgentManager,
        obs_service: ObservabilityService,
        app_config: Optional[AppConfig] = None,
    ):
        self.chat_service = chat_service
        self.agent_mgr = agent_mgr
        self.obs_service = obs_service
        self.eval_agent = self._build_eval_agent(app_config or None, agent_mgr)
        self.run_config = agent_mgr.run_config

        # Simple built-in cases; can be extended.
        self.default_cases: List[EvalCase] = [
            EvalCase(
                name="flight_status_basic",
                user_message="What's the status of flight ABC123?",
                expected="Provide current status or ask for missing flight/confirmation numbers.",
                context={"flight_number": "ABC123"},
            ),
            EvalCase(
                name="food_order",
                user_message="I'd like to order a vegetarian meal.",
                expected="Confirm vegetarian meal and place the order.",
                context={"meal_preference": "vegetarian"},
                history=[
                    {"role": "assistant", "content": "Hi, how can I assist you with your flight today?"},
                    {"role": "user", "content": "Do you have vegetarian options?"},
                ],
            ),
            EvalCase(
                name="faq_refund",
                user_message="What is your refund policy for delayed flights?",
                expected="Summarize refund policy for delays.",
            ),
        ]

    def _build_eval_agent(self, app_config: Optional[AppConfig], agent_mgr: AgentManager):
        if app_config and app_config.eval_llm:
            eval_cfg = app_config.eval_llm
            client = AsyncOpenAI(base_url=eval_cfg.base_url, api_key=eval_cfg.api_key)
            model = OpenAIChatCompletionsModel(model=eval_cfg.model_name, openai_client=client)
            return build_eval_agent(model)
        return build_eval_agent(agent_mgr.model)

    async def run_cases(self, cases: Optional[List[EvalCase]] = None, use_latest_only: bool = True) -> List[Dict[str, Any]]:
        cases = cases or self.default_cases
        results: List[Dict[str, Any]] = []

        for case in cases:
            # Build conversation state with optional context and history
            ctx = create_initial_context()
            if case.context:
                for k, v in case.context.items():
                    if hasattr(ctx, k):
                        setattr(ctx, k, v)

            history = case.history or []
            triage = self.agent_mgr.get_agent_by_role(AgentRole.TRIAGE)
            state = ConversationState(
                state_id=f"offline-{case.name}",
                input_items=list(history),
                current_agent_name=triage.name,
                context=ctx,
            )

            chat_res = await self.chat_service.chat_with_state(state, case.user_message, persist=False)
            assistant_outputs = [m.get("content", "") for m in (chat_res.get("messages") or [])]
            assistant_text = "\n".join([t for t in assistant_outputs if t])
            trace_id = chat_res.get("trace_id")

            # Build judge input
            judge_input = (
                f"User message: {case.user_message}\n"
                f"Assistant reply: {assistant_text}\n"
            )
            if case.expected:
                judge_input += f"Expected behavior: {case.expected}\n"

            # Reuse the trace from chat (per round) and push scores there
            if not trace_id:
                trace_id = f"offline-{case.name}"
                
            judge_result = await Runner.run(
                self.eval_agent,
                [{"role": "user", "content": judge_input}],
                context=None,
                run_config=self.run_config,
            )
            scores = judge_result.final_output_as(EvalScores)
            eval_trace_id = self.obs_service.log_eval_trace(
                conversation_id="NO Conversation",
                agent_name="LLM Judge",
                context={"case": case.name},
                eval_input=judge_input,
                eval_output=scores.model_dump(),
            )
            obs_ids = self._log_scores(trace_id, scores)

            results.append(
                {
                    "case": case.name,
                    "trace_id": trace_id,
                    "eval_trace_id": eval_trace_id,
                    "scores": scores.model_dump(),
                    "assistant_reply": assistant_text,
                    "score_observation_ids": obs_ids,
                }
            )

        return results

    def _log_scores(self, trace_id: str, scores: EvalScores):
        metrics = scores.model_dump()
        reasoning = metrics.pop("reasoning", None)
        obs_ids = []
        for name, value in metrics.items():
            if isinstance(value, (int, float)):
                self.obs_service.score(trace_id=trace_id, name=name, value=float(value), comment=reasoning)
                obs_ids.append(name)
        return obs_ids
