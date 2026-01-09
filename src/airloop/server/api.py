from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time

from airloop.agents.manager import AgentManager
from airloop.domain.schema import InMemoryConversationStore, PersistentConversationStore
from airloop.service.chat_service import ChatService
from airloop.service.offline_eval_service import OfflineEvalService
from airloop.service.conversation_eval_service import ConversationEvalService, ConversationEvalRequest
from airloop.service.feedback_service import FeedbackService
from airloop.service.auth_service import AuthService
from airloop.service.data_service import DataService
from airloop.settings import load_app_config
from airloop.service.observility_service import LangfuseObservabilityService, NoopObservabilityService
from airloop.domain.schema import FeedbackRequest
from fastapi import Query
from airloop.service.chat_service import ROLES_TO_SHOW

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    user_id: Optional[int] = None
    message: str

class LoginRequest(BaseModel):
    username: str
    password: str

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
    auth_svc = AuthService(cfg.store.path)
    auth_svc.init_db()
    data_svc = DataService(cfg.store.path)
    data_svc.init_db()
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
        if req.user_id is None:
            raise HTTPException(status_code=400, detail="user_id required")
        user = auth_svc.get_user_by_id(req.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")
        return await chat_svc.chat(
            req.conversation_id,
            req.message,
            req.user_id,
            user_name=user.get("username"),
            account_number=user.get("account_number"),
        )

    @app.post("/api/login")
    async def login(req: LoginRequest):
        user = auth_svc.login(req.username, req.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user

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
    async def list_sessions(limit: int = 20, user_id: Optional[int] = None):
        if user_id is None:
            raise HTTPException(status_code=400, detail="user_id required")
        states = store.list(limit=limit)
        return [
            {
                "conversation_id": st.state_id,
                "current_agent": st.current_agent_name,
                "rounds": st.round_counter,
                "context": st.context,
                "messages": st.messages,
                "events": _build_events(st),
                "agents": agent_mgr.list_agents(filter=ROLES_TO_SHOW),
                "guardrails": _build_guardrails(st),
            }
            for st in states
            if st.user_id == user_id
        ]

    return app


def _build_events(state):
    events = []
    for round_id in sorted((state.round_store or {}).keys()):
        store = state.round_store[round_id]
        for ev in store.events or []:
            if isinstance(ev, dict):
                events.append(ev)
    return events

def _build_guardrails(state):
    guardrails = []
    for round_id in sorted((state.round_store or {}).keys()):
        store = state.round_store[round_id]
        for gr in store.guardrails or []:
            if isinstance(gr, dict):
                guardrails.append(gr)
    return guardrails

app = create_app()
