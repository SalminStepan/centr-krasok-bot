from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request

from src.ai.assistant import CompanyAssistant
from src.storage.conversation import ConversationStore


LOGGER = logging.getLogger(__name__)


class TelegramBot:
    def __init__(
        self,
        token: str,
        assistant: CompanyAssistant,
        conversations: ConversationStore,
    ) -> None:
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not configured")
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.assistant = assistant
        self.conversations = conversations

    def run_polling(self) -> None:
        offset = 0
        LOGGER.info("Telegram polling started")
        while True:
            updates = self._get_updates(offset)
            for update in updates:
                offset = max(offset, update["update_id"] + 1)
                self._handle_update(update)
            time.sleep(0.5)

    def _handle_update(self, update: dict) -> None:
        message = update.get("message") or {}
        text = (message.get("text") or "").strip()
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if not chat_id or not text:
            return

        self._send_chat_action(chat_id, "typing")
        history = self.conversations.get(chat_id)
        answer = self.assistant.answer(text, history)
        self.conversations.append(chat_id, "user", text)
        self.conversations.append(chat_id, "assistant", answer)
        self._send_message(chat_id, answer)

    def _get_updates(self, offset: int) -> list[dict]:
        params = urllib.parse.urlencode({"timeout": 25, "offset": offset, "allowed_updates": '["message"]'})
        response = self._request("GET", f"{self.api_url}/getUpdates?{params}")
        return response.get("result", [])

    def _send_message(self, chat_id: int, text: str) -> None:
        self._request(
            "POST",
            f"{self.api_url}/sendMessage",
            {"chat_id": chat_id, "text": text[:4000], "disable_web_page_preview": True},
        )

    def _send_chat_action(self, chat_id: int, action: str) -> None:
        self._request("POST", f"{self.api_url}/sendChatAction", {"chat_id": chat_id, "action": action})

    @staticmethod
    def _request(method: str, url: str, payload: dict | None = None) -> dict:
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=35) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            LOGGER.warning("Telegram API request failed: %s", exc)
            return {"ok": False, "result": []}
