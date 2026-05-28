# Деплой на сервер

Пример рассчитан на Ubuntu/Debian и запуск через `systemd`.

## 1. Подготовить сервер

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
sudo useradd --system --create-home --shell /usr/sbin/nologin centrbot || true
```

## 2. Склонировать проект

```bash
sudo git clone git@github.com:SalminStepan/centr-krasok-bot.git /opt/centr-krasok-bot
sudo chown -R centrbot:centrbot /opt/centr-krasok-bot
```

Если на сервере нет SSH-ключа для GitHub, можно клонировать публичный репозиторий по HTTPS:

```bash
sudo git clone https://github.com/SalminStepan/centr-krasok-bot.git /opt/centr-krasok-bot
sudo chown -R centrbot:centrbot /opt/centr-krasok-bot
```

## 3. Установить зависимости

```bash
cd /opt/centr-krasok-bot
sudo -u centrbot python3 -m venv .venv
sudo -u centrbot .venv/bin/pip install -r requirements.txt
```

## 4. Создать `.env`

```bash
sudo -u centrbot cp .env.example .env
sudo -u centrbot nano .env
```

Заполнить реальные значения:

```env
TELEGRAM_BOT_TOKEN=...
AI_API_KEY=...
AI_API_BASE=https://openrouter.ai/api/v1
AI_MODEL=openrouter/free
AI_TEMPERATURE=0.2
KNOWLEDGE_BASE_PATH=data/processed/knowledge_base.json
CONVERSATION_STORE_PATH=data/runtime/conversations.json
MAX_DIALOG_MESSAGES=8
```

## 5. Подключить systemd

```bash
sudo cp deploy/centr-krasok-bot.service /etc/systemd/system/centr-krasok-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now centr-krasok-bot
```

## 6. Проверить работу

```bash
sudo systemctl status centr-krasok-bot
sudo journalctl -u centr-krasok-bot -f
```

## Обновление после новых коммитов

```bash
cd /opt/centr-krasok-bot
sudo -u centrbot git pull
sudo -u centrbot .venv/bin/pip install -r requirements.txt
sudo systemctl restart centr-krasok-bot
sudo journalctl -u centr-krasok-bot -f
```
