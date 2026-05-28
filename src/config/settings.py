from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parents[2]


def _load_dotenv() -> None:
    if load_dotenv:
        load_dotenv(ROOT_DIR / ".env")
        return

    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _path_from_env(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default))
    return value if value.is_absolute() else ROOT_DIR / value


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    ai_api_key: str
    ai_model: str
    ai_api_base: str
    ai_temperature: float
    knowledge_base_path: Path
    conversation_store_path: Path
    max_dialog_messages: int

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            ai_api_key=os.getenv("AI_API_KEY", ""),
            ai_model=os.getenv("AI_MODEL", "gpt-4o-mini"),
            ai_api_base=os.getenv("AI_API_BASE", "https://api.openai.com/v1").rstrip("/"),
            ai_temperature=float(os.getenv("AI_TEMPERATURE", "0.2")),
            knowledge_base_path=_path_from_env(
                "KNOWLEDGE_BASE_PATH", "data/processed/knowledge_base.json"
            ),
            conversation_store_path=_path_from_env(
                "CONVERSATION_STORE_PATH", "data/runtime/conversations.json"
            ),
            max_dialog_messages=int(os.getenv("MAX_DIALOG_MESSAGES", "8")),
        )
