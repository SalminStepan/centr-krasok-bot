from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


class AIClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenAICompatibleClient:
    api_key: str
    api_base: str
    model: str
    temperature: float = 0.2

    def chat(self, messages: list[dict[str, str]]) -> str:
        if not self.api_key:
            raise AIClientError("AI_API_KEY is not configured")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        request = urllib.request.Request(
            f"{self.api_base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise AIClientError(str(exc)) from exc

        try:
            content = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise AIClientError("Unexpected AI API response") from exc
        if not content:
            raise AIClientError("AI returned an empty response")
        return content
