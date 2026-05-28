from __future__ import annotations

import re

from src.ai.client import AIClientError, OpenAICompatibleClient
from src.ai.responses import (
    AI_ERROR_REPLY,
    CONTACTS_REPLY,
    GREETING_REPLY,
    IRRELEVANT_REPLY,
    SOCIAL_MEDIA_REPLY,
    UNKNOWN_REPLY,
    WORKING_HOURS_REPLY,
    glossary_reply,
)
from src.company_knowledge.retriever import KnowledgeRetriever, SearchResult
from src.storage.conversation import Message


SYSTEM_PROMPT = """Ты дружелюбный Telegram-ассистент компании «Центр Красок #1».
Отвечай только на основе блока «База знаний».
Не выдумывай факты, цены, вакансии, наличие товаров, имена клиентов или условия,
которых нет в базе.
Если данных недостаточно, честно скажи: «В моей базе нет подтвержденной информации».
Если вопрос не относится к компании, мягко верни разговор к «Центру Красок #1».
Не используй XML/HTML-теги, markdown-разметку ролей или служебные маркеры.
Отвечай кратко, понятно, на русском языке."""

START_MESSAGES = {"/start", "start", "старт", "привет", "здравствуйте", "добрый день"}
CONTACT_WORDS = ("контакт", "адрес", "телефон", "почта", "email")
HOURS_WORDS = ("время работы", "режим", "график", "работаете")
SOCIAL_WORDS = ("соц", "соцсет", "социальн", "instagram", "инстаграм", "facebook", "youtube")
SERVICE_WORDS = (
    "центр красок",
    "centr-krasok",
    "centr_krasok",
    "краск",
    "лкм",
    "лак",
    "эмал",
    "грунт",
    "штукатур",
    "обои",
    "растворител",
    "маляр",
    "колеров",
    "оттен",
    "цвет",
    "dulux",
    "marshall",
    "masterline",
    "hammerite",
    "pinotex",
    "luxium",
    "dufa",
    "oikos",
    "profilux",
    "vetonit",
    "hygge",
    "соц",
    "соцсет",
    "социальн",
    "instagram",
    "инстаграм",
    "facebook",
    "youtube",
)
COMPANY_INTENT_WORDS = (
    "адрес",
    "где находится",
    "офис",
    "салон",
    "контакт",
    "телефон",
    "почта",
    "email",
    "режим",
    "график",
    "услуг",
    "достав",
    "самовывоз",
    "каталог",
    "товар",
    "продукт",
    "бренд",
    "технолог",
    "дизайнер",
    "строител",
    "партнер",
    "клиент",
    "ваканс",
    "работа",
    "алматы",
    "астана",
    "новост",
    "акци",
    "соцсет",
    "социальн",
)
GENERIC_COMPANY_QUESTIONS = (
    "чем занимается компания",
    "что делает компания",
    "о компании",
    "расскажи про компанию",
    "кто они",
)


class CompanyAssistant:
    def __init__(self, retriever: KnowledgeRetriever, ai_client: OpenAICompatibleClient) -> None:
        self.retriever = retriever
        self.ai_client = ai_client

    def answer(self, user_text: str, history: list[Message]) -> str:
        text = user_text.strip()
        if not text:
            return UNKNOWN_REPLY
        if self._is_start_message(text):
            return GREETING_REPLY

        fixed_reply = self._fixed_reply(text)
        if fixed_reply:
            return fixed_reply
        if not self._looks_company_related(text, history):
            return IRRELEVANT_REPLY

        results = self.retriever.search(self._build_retrieval_query(text, history))
        if not self._is_relevant(results):
            return UNKNOWN_REPLY

        try:
            answer = self.ai_client.chat(self._build_messages(text, history, results))
        except AIClientError:
            return AI_ERROR_REPLY
        return self._with_contact_fallback(self._sanitize_model_answer(answer))

    @staticmethod
    def _is_start_message(user_text: str) -> bool:
        return user_text.lower() in START_MESSAGES

    @staticmethod
    def _fixed_reply(user_text: str) -> str | None:
        text = user_text.lower()
        if any(word in text for word in CONTACT_WORDS):
            return CONTACTS_REPLY
        if any(word in text for word in HOURS_WORDS):
            return WORKING_HOURS_REPLY
        if any(word in text for word in SOCIAL_WORDS):
            return SOCIAL_MEDIA_REPLY
        return glossary_reply(text)

    @staticmethod
    def _looks_company_related(user_text: str, history: list[Message]) -> bool:
        text = user_text.lower()
        if any(word in text for word in SERVICE_WORDS):
            return True
        if any(word in text for word in COMPANY_INTENT_WORDS):
            return True
        if any(phrase in text for phrase in GENERIC_COMPANY_QUESTIONS):
            return True

        recent_context = " ".join(item.content.lower() for item in history[-4:])
        has_company_context = any(word in recent_context for word in SERVICE_WORDS)
        return has_company_context and len(text.split()) <= 8

    @staticmethod
    def _build_retrieval_query(user_text: str, history: list[Message]) -> str:
        recent_user_messages = [item.content for item in history if item.role == "user"][-2:]
        return " ".join([*recent_user_messages, user_text])

    @staticmethod
    def _is_relevant(results: list[SearchResult]) -> bool:
        return bool(results and results[0].score >= 1.2)

    @staticmethod
    def _build_messages(
        user_text: str, history: list[Message], results: list[SearchResult]
    ) -> list[dict[str, str]]:
        knowledge = "\n\n".join(
            f"[{item.chunk.title}]\n{item.chunk.text}\nИсточники: {', '.join(item.chunk.source_urls)}"
            for item in results
        )
        compact_history = [
            {"role": item.role, "content": item.content}
            for item in history[-6:]
            if item.role in {"user", "assistant"}
        ]
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"База знаний:\n{knowledge}"},
            *compact_history,
            {"role": "user", "content": user_text},
        ]

    @staticmethod
    def _sanitize_model_answer(answer: str) -> str:
        cleaned = answer.strip()
        cleaned = re.sub(r"</?(assistant|user|system)\s*>", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^(assistant|ассистент)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned or UNKNOWN_REPLY

    @staticmethod
    def _with_contact_fallback(answer: str) -> str:
        if "нет подтвержденной информации" not in answer.lower():
            return answer
        if "centr-krasok.kz" in answer and "+7 778 061 5000" in answer:
            return answer
        return (
            f"{answer}\n\n"
            "Сайт: https://centr-krasok.kz/\n"
            "Основной телефон: +7 778 061 5000"
        )
