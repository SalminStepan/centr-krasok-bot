from pathlib import Path

from src.ai.assistant import CompanyAssistant
from src.ai.responses import (
    CONTACTS_REPLY,
    IRRELEVANT_REPLY,
    PRODUCTS_REPLY,
    SOCIAL_MEDIA_REPLY,
    WORKING_HOURS_REPLY,
)
from src.company_knowledge.retriever import KnowledgeRetriever
from src.storage.conversation import Message


class FakeAIClient:
    def chat(self, messages: list[dict[str, str]]) -> str:
        return "AI called"


def build_assistant() -> CompanyAssistant:
    retriever = KnowledgeRetriever.from_json(Path("data/processed/knowledge_base.json"))
    return CompanyAssistant(retriever, FakeAIClient())


def test_rejects_irrelevant_questions_before_ai() -> None:
    assistant = build_assistant()
    assert assistant.answer("Сколько весит 1 кг золота?", []) == IRRELEVANT_REPLY
    assert assistant.answer("Что такое золото?", []) == IRRELEVANT_REPLY


def test_uses_fixed_contact_and_hours_replies() -> None:
    assistant = build_assistant()
    assert assistant.answer("Ваши контакты и адреса", []) == CONTACTS_REPLY
    assert assistant.answer("Время работы", []) == WORKING_HOURS_REPLY
    assert assistant.answer("Соц сети", []) == SOCIAL_MEDIA_REPLY
    assert assistant.answer("Какой у вас ассортимент?", []) == PRODUCTS_REPLY


def test_sanitizes_markdown_artifacts() -> None:
    assistant = build_assistant()
    cleaned = assistant._sanitize_model_answer(
        "Компания продает **интерьерные краски**. Подробнее: [каталог](https://centr-krasok.kz/catalog/)"
    )
    assert "**" not in cleaned
    assert "[каталог]" not in cleaned
    assert "каталог: https://centr-krasok.kz/catalog/" in cleaned


def test_glossary_answers_known_terms_only() -> None:
    assistant = build_assistant()
    answer = assistant.answer("Что такое лак?", [])
    assert "Лак —" in answer
    assert "золото" not in answer.lower()


def test_short_follow_up_uses_company_context() -> None:
    assistant = build_assistant()
    history = [
        Message(role="user", content="Где находятся салоны Центр Красок?"),
        Message(role="assistant", content="Салоны есть в Алматы и Астане."),
    ]
    assert assistant.answer("А в Астане?", history) == "AI called"
