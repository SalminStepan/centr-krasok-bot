from pathlib import Path

from src.company_knowledge.retriever import KnowledgeRetriever


def test_retriever_finds_contacts() -> None:
    retriever = KnowledgeRetriever.from_json(Path("data/processed/knowledge_base.json"))
    results = retriever.search("Где находится офис в Алматы?")
    assert results
    assert results[0].chunk.id == "contacts"


def test_retriever_finds_vacancies() -> None:
    retriever = KnowledgeRetriever.from_json(Path("data/processed/knowledge_base.json"))
    results = retriever.search("Какие есть вакансии?")
    assert results
    assert results[0].chunk.id == "vacancies"
