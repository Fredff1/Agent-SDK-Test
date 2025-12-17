from __future__ import annotations as _annotations

import random
from pydantic import BaseModel
import string


# qwen model for agent construction
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, Model, ModelProvider,RunConfig, ModelSettings,set_tracing_disabled

class QwenModelProvider(ModelProvider):
        
    def get_model(self, model_name: str | None, client: AsyncOpenAI) -> Model:
        return OpenAIChatCompletionsModel(model=model_name , client=client)
    
def build_qwen3_run_config(
    provider: QwenModelProvider,
    enable_thinking: bool = True,
) -> RunConfig:
    mt = ModelSettings(extra_body = {"enable_thinking": enable_thinking}) 
    cfg = RunConfig(model_provider=provider, model_settings=mt)
    return cfg
    
    