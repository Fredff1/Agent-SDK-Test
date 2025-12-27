from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from airloop.agents.manager import AgentManager
from airloop.domain.schema import InMemoryConversationStore
from airloop.service.chat_service import ChatService
from airloop.settings import load_app_config
from airloop.service.observility_service import LangfuseObservabilityService, NoopObservabilityService

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
    store = InMemoryConversationStore()
    obs_service = LangfuseObservabilityService(cfg.langfuse) if cfg.langfuse else NoopObservabilityService()
    chat_svc = ChatService(agent_mgr, store, obs_service)

    @app.post("/api/chat")
    async def chat(req: ChatRequest):
        return await chat_svc.chat(req.conversation_id, req.message)

    return app

app = create_app()
