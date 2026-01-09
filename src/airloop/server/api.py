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
    order_id: Optional[int] = None
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
    auth_svc = AuthService(cfg.store.path)
    auth_svc.init_db()
    data_svc = DataService(cfg.store.path)
    data_svc.init_db()
    agent_mgr = AgentManager(cfg.llm, data_svc)
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
        order_info = None
        if req.order_id is not None:
            order_info = data_svc.get_order(req.order_id, req.user_id)
            if not order_info:
                raise HTTPException(status_code=404, detail="Order not found")
            if order_info.get("status") == "canceled":
                raise HTTPException(status_code=410, detail="Order is canceled")
        if req.conversation_id is None and req.order_id is None:
            raise HTTPException(status_code=400, detail="order_id required for new session")
        return await chat_svc.chat(
            req.conversation_id,
            req.message,
            req.user_id,
            user_name=user.get("username"),
            account_number=user.get("account_number"),
            order_id=order_info["id"] if order_info else None,
            confirmation_number=order_info["confirmation_number"] if order_info else None,
            flight_number=order_info["flight_number"] if order_info else None,
            seat_number=str(order_info["seat_number"]) if order_info else None,
        )

    @app.post("/api/login")
    async def login(req: LoginRequest):
        user = auth_svc.login(req.username, req.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user

    @app.get("/api/orders")
    async def list_orders(user_id: Optional[int] = None):
        if user_id is None:
            raise HTTPException(status_code=400, detail="user_id required")
        if not auth_svc.get_user_by_id(user_id):
            raise HTTPException(status_code=401, detail="Invalid user")
        return data_svc.list_orders(user_id)

    @app.post("/api/orders")
    async def create_order(user_id: Optional[int] = None):
        if user_id is None:
            raise HTTPException(status_code=400, detail="user_id required")
        if not auth_svc.get_user_by_id(user_id):
            raise HTTPException(status_code=401, detail="Invalid user")
        try:
            return data_svc.create_order(user_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

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
                "title": _ensure_session_title(st, store),
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

def _ensure_session_title(state, store):
    if state.title:
        return state.title
    confirmation = None
    if hasattr(state.context, "confirmation_number"):
        confirmation = state.context.confirmation_number
    if confirmation:
        state.title = f"Order {confirmation}"
    else:
        state.title = f"Session {state.state_id[:6]}"
    store.save(state.state_id, state)
    return state.title

app = create_app()
