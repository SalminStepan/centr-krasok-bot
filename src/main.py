from __future__ import annotations

import logging

from src.ai.assistant import CompanyAssistant
from src.ai.client import OpenAICompatibleClient
from src.bot.telegram import TelegramBot
from src.company_knowledge.retriever import KnowledgeRetriever
from src.config.settings import Settings
from src.storage.conversation import ConversationStore


def build_bot() -> TelegramBot:
    settings = Settings.from_env()
    retriever = KnowledgeRetriever.from_json(settings.knowledge_base_path)
    ai_client = OpenAICompatibleClient(
        api_key=settings.ai_api_key,
        api_base=settings.ai_api_base,
        model=settings.ai_model,
        temperature=settings.ai_temperature,
    )
    assistant = CompanyAssistant(retriever=retriever, ai_client=ai_client)
    conversations = ConversationStore(
        path=settings.conversation_store_path,
        max_messages=settings.max_dialog_messages,
    )
    return TelegramBot(
        token=settings.telegram_bot_token,
        assistant=assistant,
        conversations=conversations,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    build_bot().run_polling()


if __name__ == "__main__":
    main()
