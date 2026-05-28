# AI Telegram Assistant для Центр Красок #1

MVP Telegram-бота, который отвечает на обычные сообщения пользователя на основе локальной базы знаний о компании.

## Что уже собрано

- Сырые HTML и текстовые выгрузки сайта: `data/raw/pages/`
- Индекс источников: `data/raw/sources_manifest.json`
- Заметки по внешнему поиску и соцсетям: `data/raw/external_research_notes.md`
- Очищенные факты: `data/processed/company_facts.md`
- База знаний для AI: `data/processed/knowledge_base.json`

## Запуск

1. Установить зависимости:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Создать `.env` по примеру:

```bash
cp .env.example .env
```

3. Заполнить:

```env
TELEGRAM_BOT_TOKEN=...
AI_API_KEY=...
AI_API_BASE=https://openrouter.ai/api/v1
AI_MODEL=openrouter/free
```

4. Запустить бота:

```bash
python3 -m src.main
```

## Обновление данных

```bash
python3 scripts/scrape_company.py
```

Скрипт сохраняет сырые HTML и очищенный текст в `data/raw/pages/`, а список источников в `data/raw/sources_manifest.json`.

## Защита от галлюцинаций

Бот ищет релевантные блоки в `data/processed/knowledge_base.json` и передает AI только найденные фрагменты. В системном промпте запрещено выдумывать факты, цены, вакансии, наличие товаров, клиентов и условия. Если данных нет, бот должен честно сказать, что в базе нет подтвержденной информации.

Для контактов, режима работы и глоссария используются готовые ответы. Так формат не зависит от модели, а вопросы не по теме отсекаются до обращения к AI API.
