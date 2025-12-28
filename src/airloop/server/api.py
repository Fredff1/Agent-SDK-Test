from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from airloop.agents.manager import AgentManager
from airloop.domain.schema import InMemoryConversationStore, PersistentConversationStore
from airloop.service.chat_service import ChatService
from airloop.service.offline_eval_service import OfflineEvalService
from airloop.service.conversation_eval_service import ConversationEvalService, ConversationEvalRequest
from airloop.service.feedback_service import FeedbackService
from airloop.settings import load_app_config
from airloop.service.observility_service import LangfuseObservabilityService, NoopObservabilityService
from airloop.domain.schema import FeedbackRequest
from fastapi import Query

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str

def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    cfg = load_app_config()
    agent_mgr = AgentManager(cfg.llm)
    if cfg.store.kind == "sqlite":
        store = PersistentConversationStore(cfg.store.path)
    else:
        store = InMemoryConversationStore()
    obs_service = LangfuseObservabilityService(cfg.langfuse) if cfg.langfuse else NoopObservabilityService()
    chat_svc = ChatService(agent_mgr, store, obs_service)
    feedback_svc = FeedbackService(obs_service)
    offline_eval_svc = OfflineEvalService(chat_svc, agent_mgr, obs_service, cfg)
    convo_eval_svc = ConversationEvalService(store, agent_mgr, obs_service, cfg)

    @app.post("/api/chat")
    async def chat(req: ChatRequest):
        return await chat_svc.chat(req.conversation_id, req.message)

    @app.post("/api/feedback")
    async def feedback(req: FeedbackRequest):
        return feedback_svc.submit(req)

    @app.post("/api/offline_eval")
    async def offline_eval(run_all: bool = Query(default=True)):
        return await offline_eval_svc.run_cases()

    @app.post("/api/conversation_eval")
    async def conversation_eval(req: ConversationEvalRequest):
        return await convo_eval_svc.evaluate_conversations(req)

    @app.get("/api/sessions")
    async def list_sessions(limit: int = 20):
        states = store.list(limit=limit)
        return [
            {
                "conversation_id": st.state_id,
                "current_agent": st.current_agent_name,
                "rounds": st.round_counter,
                "context": st.context,
            }
            for st in states
        ]

    return app

app = create_app()
