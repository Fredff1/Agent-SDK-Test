from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from airloop.settings import UserConfig
from airloop.agents.manager import AgentManager
from airloop.domain.schema import InMemoryConversationStore
from airloop.service.chat_service import ChatService

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

    cfg = UserConfig(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key="sk-f55837467fd543a49cfc5cecd003d788",
        model_name="qwen3-next-80b-a3b-instruct",
    )
    agent_mgr = AgentManager(cfg)
    store = InMemoryConversationStore()
    chat_svc = ChatService(agent_mgr, store)

    @app.post("/api/chat")
    async def chat(req: ChatRequest):
        return await chat_svc.chat(req.conversation_id, req.message)

    return app

app = create_app()
