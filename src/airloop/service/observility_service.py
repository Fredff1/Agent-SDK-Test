from __future__ import annotations

from typing import Any, Dict, Optional, List, Iterator
from uuid import uuid4
from contextlib import contextmanager
import traceback
import time

from langfuse import Langfuse, get_client, LangfuseSpan

from airloop.settings import LangfuseConfig



class ObservabilityService:
    
    @contextmanager
    def start_round_trace(
        self,
        *,
        conversation_id: str,
        round_id: int,
        input_messages: str,
        agent_name: str,
        context: Dict[str, Any],
        **kwargs,
    ) -> Iterator[str]:
        raise NotImplementedError

    def log_round(self, *, trace_id: str, messages: Any, events: Any, next_agent: str | None, context: Dict[str, Any], **kwargs) -> None:
        raise NotImplementedError

    def log_guardrail_trip(self, *, trace_id: str, reason: str, **kwargs) -> None:
        raise NotImplementedError

    def score(self, *, trace_id: str, name: str, value: float, comment: str | None = None, **kwargs) -> None:
        raise NotImplementedError


class NoopObservabilityService(ObservabilityService):
    def __init__(self) -> None:
        self.enabled = False

    @contextmanager
    def start_round_trace(
        self,
        *,
        conversation_id: str,
        round_id: int,
        input_messages: str,
        agent_name: str,
        context: Dict[str, Any],
        **kwargs
    ) -> Iterator[str]:
        trace_id =uuid4().hex
        try:
            yield trace_id
        finally:
            return 

    def log_round(self, *, trace_id: str, messages: Any, events: Any, next_agent: str | None, context: Dict[str, Any], **kwargs) -> None:
        return None

    def log_guardrail_trip(self, *, trace_id: str, reason: str, **kwargs) -> None:
        return None

    def score(self, *, trace_id: str, name: str, value: float, comment: str | None = None, **kwargs) -> None:
        return None


class LangfuseObservabilityService(ObservabilityService):
    def __init__(self, config: LangfuseConfig):
        self.config = config
        self.enabled = True
        self.client = Langfuse(
            public_key=config.public_key,
            secret_key=config.secret_key,
            host=config.host,
            release=getattr(config, "release", None),
        )

        self._round_ctx: Dict[str, Dict[str, Any]] = {}

    @contextmanager
    def start_round_trace(
        self,
        *,
        conversation_id: str,
        round_id: int,
        input_messages: str,
        agent_name: str,
        context: Dict[str, Any],
        **kwargs,
    ) -> Iterator[str]:
        trace_id = uuid4().hex

        # ✅ 用 start_as_current_observation 才能让它成为“当前根”
        with self.client.start_as_current_observation(
            as_type="span",
            name="chat_round",
            trace_context={"trace_id": trace_id},
        ) as root:
            try:
                # 进入时：写 root 信息
                root.update(
                    metadata={
                        "conversation_id": conversation_id,
                        "round_id": round_id,
                        "agent_name": agent_name,
                        "begin_context": context,
                    },
                )

                # ✅ 这里继续保留你原先的 dctx / root_span_id / root_obj
                root_span_id = root.id
                self._round_ctx[trace_id] = {
                    "trace_id": trace_id,
                    "root_span_id": root_span_id,
                    "root_obj": root,
                    # 如果你后面还想用更多信息，这里也可以继续塞
                }

                # ✅ 把 trace_id 交给外层 with，用法不变：as trace_id
                yield trace_id

            finally:
                # 退出时：自动清理（不影响你 with 内的所有 log_xxx 功能）
                # self._round_ctx.pop(trace_id, None)
                try:
                    self.client.flush()
                except Exception:
                    traceback.print_exc()
    def log_round(
        self,
        *,
        conversation_id: str,
        trace_id: str,
        messages: Any,
        events: List[Dict[str, Any]],
        next_agent: Optional[str],
        context: Dict[str, Any],
        input_content: List[Dict[str,str]],
        **kwargs
    ) -> None:
        ctx = self._round_ctx.get(trace_id)
        if not ctx:
            return

        root: LangfuseSpan = ctx.get("root_obj")

        try:
            for e in (events or []):
                etype = e.get("type")
                name = f"event:{etype or 'unknown'}"

                # tool_call / tool_output / handoff：用 span
                if etype in ("tool_call", "tool_output", "handoff"):
                    with self.client.start_as_current_observation(
                        as_type="span",
                        name=name,
                        # trace_context={"trace_id": trace_id, "parent_span_id": root_span_id},
                    ) as sp:
                        e["observation_id"]=sp.id
                        e["langfuse_type"] = "span"
                        sp.update(
                            input={
                                "input_messages": input_content,

                            },
                            output={
                                "content": e.get("content")
                            },
                            metadata={
                                "dtype": etype,
                                "conversation_id":conversation_id,
                                "event_id": e.get("id"),
                                "timestamp_ms": e.get("timestamp"),
                                "metadata": e.get("metadata"),
                                "agent": e.get("agent"),
                            },
                        )

                # message：如果你想在 UI 里像“输出”，用 generation
                elif etype == "message":
                    with self.client.start_as_current_observation(
                        as_type="generation",
                        name="assistant_message",
                        # trace_context={"trace_id": trace_id, "parent_span_id": root_span_id},
                    ) as gen:
                        e["observation_id"]=gen.id
                        e["langfuse_type"] = "gen"
                        gen.update(
                            # 你这里没有 model/prompt，就先别填 model
                            input={
                                # 把“这轮上下文”或“触发它的 user message”等放 metadata 也行
                                "input_messages": input_content,
                            },
                            output=e.get("content"),
                            metadata={
                                "dtype": etype,
                                "conversation_id":conversation_id,
                                "agent": e.get("agent"),
                                "event_id": e.get("id"),
                                "timestamp_ms": e.get("timestamp"),
                            },
                        )

                else:
                    # 其他未知类型：兜底 span
                    with self.client.start_as_current_observation(
                        as_type="span",
                        name="event:other",
                        # trace_context={"trace_id": trace_id, "parent_span_id": root_span_id},
                    ) as sp:
                        e["observation_id"]=sp.id
                        e["langfuse_type"] = "span"
                        sp.update(
                            input={"raw_event": e},
                            metadata={"timestamp_ms": e.get("timestamp"),"conversation_id":conversation_id,},
                        )
                time.sleep(0.05)

            # 2) 整轮汇总：单独放一个 span，方便 UI 一眼看全
            # with self.client.start_as_current_observation(
            #     as_type="span",
            #     name="round_summary",
            #     # trace_context={"trace_id": trace_id, "parent_span_id": root_span_id},
            # ) as summary:
            root.update(
                input=input_content,
                output=messages,
                metadata={"after_context": context, "next_agent": next_agent,"events": events},
            )

        except Exception as e:
            # 不要完全吞：至少可以在本地 log 一下
            # logging.exception("Langfuse log_round failed")
            traceback.print_exc()
            return

    def log_guardrail_trip(self, *, trace_id: str, reason: str) -> None:
        ctx = self._round_ctx.get(trace_id)
        if not ctx:
            return
        root_span_id: str = ctx.get("root_span_id", "")

        try:
            with self.client.start_as_current_observation(
                as_type="span",
                name="guardrail_trip",
                # trace_context={"trace_id": trace_id, "parent_span_id": root_span_id},
            ) as sp:
                sp.update(metadata={"reason": reason})

            # # v3 的 score 一般是 “current trace/span” 的概念：需要进入上下文
            # with self.client.start_as_current_observation(
            #     as_type="span",
            #     name="guardrail_score_ctx",
            #     # trace_context={"trace_id": trace_id, "parent_span_id": root_span_id},
            # ):
            #     self.client.score_current_trace(name="guardrail_trip", value=0.0, comment=reason)

        except Exception:
            traceback.print_exc()
            return



    def score(
        self,
        *,
        trace_id: str,
        name: str,
        value: float,
        comment: str | None = None,
        **kwargs,
    ) -> None:
        try:
            self.client.create_score(trace_id=trace_id, name=name, value=value, comment=comment)
        except Exception:
            traceback.print_exc()
