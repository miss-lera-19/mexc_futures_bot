# MEXC Futures Bot (Stable PTB Version)

Цей бот аналізує ринок кожну хвилину для монет BTC, ETH, SOL і надсилає сигнали LONG/SHORT при сильних умовах (RSI, EMA-перетин). Побудовано на `python-telegram-bot`.

## Команди:
- `/start` — активувати бота
- `/signal` — вручну отримати аналіз усіх монет

## Інструкція запуску на Render:
1. Створи репозиторій на GitHub
2. Додай файли з цього архіву
3. На Render обери:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
4. Додай ENV-перемінні або `.env`

Бот працює без aiohttp та сумісний із безкоштовним Render.