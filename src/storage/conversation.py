from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Message:
    role: str
    content: str


class ConversationStore:
    def __init__(self, path: Path, max_messages: int = 8) -> None:
        self.path = path
        self.max_messages = max_messages
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def get(self, chat_id: int) -> list[Message]:
        data = self._read()
        return [Message(**item) for item in data.get(str(chat_id), [])]

    def append(self, chat_id: int, role: str, content: str) -> None:
        data = self._read()
        messages = data.get(str(chat_id), [])
        messages.append(asdict(Message(role=role, content=content)))
        data[str(chat_id)] = messages[-self.max_messages :]
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _read(self) -> dict[str, list[dict[str, str]]]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
