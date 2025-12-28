from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from agents import Runner
from pydantic import BaseModel

from airloop.agents.eval_agent import build_eval_agent, EvalScores
from airloop.agents.manager import AgentManager
from airloop.domain.schema import ConversationStore, ConversationState
from airloop.service.observility_service import ObservabilityService
from airloop.settings import AppConfig
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel


class ConversationEvalRequest(BaseModel):
    conversation_ids: List[str]
    mode: str = "latest"  # "latest" or "all"


class ConversationEvalService:
    """
    Evaluate existing conversations using a local LLM judge (no Langfuse evaluator API).
    For each round, scores are written via ObservabilityService.score to the existing trace_id.
    """

    def __init__(self, store: ConversationStore, agent_mgr: AgentManager, obs_service: ObservabilityService, app_config: Optional[AppConfig] = None):
        self.store = store
        self.obs = obs_service
        self.judge = self._build_eval_agent(app_config, agent_mgr)
        self.run_config = agent_mgr.run_config

    def _build_eval_agent(self, app_config: Optional[AppConfig], agent_mgr: AgentManager):
        if app_config and app_config.eval_llm:
            eval_cfg = app_config.eval_llm
            client = AsyncOpenAI(base_url=eval_cfg.base_url, api_key=eval_cfg.api_key)
            model = OpenAIChatCompletionsModel(model=eval_cfg.model_name, openai_client=client)
            return build_eval_agent(model)
        return build_eval_agent(agent_mgr.model)

    async def evaluate_conversations(self, req: ConversationEvalRequest) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        latest_only = req.mode != "all"

        for cid in req.conversation_ids:
            state = self.store.get(cid)
            if state is None:
                continue

            rounds = sorted(state.round_store.items(), key=lambda kv: kv[0])
            if latest_only and rounds:
                rounds = [rounds[-1]]

            for round_idx, round_store in rounds:
                trace_id = round_store.trace_id or uuid4().hex
                user_msgs = [m.get("content", "") for m in round_store.input_items if m.get("role") == "user"]
                last_user = user_msgs[-1] if user_msgs else ""
                assistant_msgs = [m.get("content", "") for m in round_store.messages]
                assistant_text = "\n".join([t for t in assistant_msgs if t])

                judge_input = (
                    f"User message: {last_user}\n"
                    f"Assistant reply: {assistant_text}\n"
                    f"Context: {state.context}"
                )

                judge_result = await Runner.run(
                    self.judge,
                    [{"role": "user", "content": judge_input}],
                    context=None,
                    run_config=self.run_config,
                )
                scores = judge_result.final_output_as(EvalScores)
                eval_trace_id = self.obs.log_eval_trace(
                    conversation_id=cid,
                    agent_name="LLM Judge",
                    context={"round": round_idx},
                    eval_input=judge_input,
                    eval_output=scores.model_dump(),
                )
                self._log_scores(trace_id, scores)

                results.append(
                    {
                        "conversation_id": cid,
                        "round": round_idx,
                        "trace_id": trace_id,
                        "eval_trace_id": eval_trace_id,
                        "scores": scores.model_dump(),
                    }
                )

        return results

    def _log_scores(self, trace_id: str, scores: EvalScores):
        metrics = scores.model_dump()
        reasoning = metrics.pop("reasoning", None)
        for name, value in metrics.items():
            if isinstance(value, (int, float)):
                self.obs.score(trace_id=trace_id, name=name, value=float(value), comment=reasoning)
