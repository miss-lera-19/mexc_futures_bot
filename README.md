# MEXC Futures Signal Bot

Telegram-бот для аналізу крипторинку (BTC, ETH, SOL) і надсилання сигналів (LONG/SHORT) через Telegram на основі технічного аналізу.

## Як запустити на Render

1. Створи GitHub-репозиторій і завантаж усі файли.
2. На [https://render.com](https://render.com) обери:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
3. Додай змінні оточення з `.env` (або залиш їх як є, якщо файл вже заповнений).
4. Запусти сервіс. Бот працює 24/7 і надсилає сигнали лише при реальних точках входу.

Контакт: @my_mexc_futures_bot