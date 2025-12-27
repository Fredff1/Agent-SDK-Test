from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import os

import yaml


@dataclass
class UserConfig:
    base_url: str
    api_key: str
    model_name: str
    output_streaming: bool = False


@dataclass
class LangfuseConfig:
    host: str
    public_key: str
    secret_key: str
    release: Optional[str] = None
    enabled: bool = True


@dataclass
class AppConfig:
    llm: UserConfig
    langfuse: Optional[LangfuseConfig] = None


def _to_bool(value: Any, default: Optional[bool] = None) -> Optional[bool]:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_app_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Load application configuration from YAML, filling missing values from environment variables.
    Environment variables take precedence when present.
    """
    cfg_path = Path(config_path or os.getenv("APP_CONFIG_PATH", "config/app.yaml")).resolve()
    raw_cfg = _load_yaml(cfg_path)

    llm_cfg = raw_cfg.get("llm", raw_cfg)
    base_url = os.getenv("LLM_BASE_URL", llm_cfg.get("base_url"))
    api_key = os.getenv("LLM_API_KEY", llm_cfg.get("api_key"))
    model_name = os.getenv("LLM_MODEL_NAME", llm_cfg.get("model_name"))
    output_streaming = _to_bool(os.getenv("LLM_OUTPUT_STREAMING", llm_cfg.get("output_streaming")), default=False)

    if not base_url or not api_key or not model_name:
        raise ValueError("Missing required LLM configuration (base_url, api_key, model_name)")

    llm = UserConfig(
        base_url=base_url,
        api_key=api_key,
        model_name=model_name,
        output_streaming=bool(output_streaming),
    )

    langfuse_cfg = raw_cfg.get("langfuse", {})
    langfuse_enabled = _to_bool(os.getenv("LANGFUSE_ENABLED", langfuse_cfg.get("enabled")), default=None)
    langfuse_host = os.getenv("LANGFUSE_HOST", langfuse_cfg.get("host"))
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY", langfuse_cfg.get("public_key"))
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY", langfuse_cfg.get("secret_key"))
    langfuse_release = os.getenv("LANGFUSE_RELEASE", langfuse_cfg.get("release"))

    langfuse = None
    has_langfuse_keys = all([langfuse_host, langfuse_public_key, langfuse_secret_key])
    if langfuse_enabled is False:
        langfuse = None
    elif has_langfuse_keys:
        langfuse = LangfuseConfig(
            host=langfuse_host,  # type: ignore[arg-type]
            public_key=langfuse_public_key,  # type: ignore[arg-type]
            secret_key=langfuse_secret_key,  # type: ignore[arg-type]
            release=langfuse_release,
            enabled=True,
        )

    return AppConfig(llm=llm, langfuse=langfuse)
    
