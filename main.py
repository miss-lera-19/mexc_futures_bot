import os
import time
import ccxt
import logging
import asyncio
from telegram import Bot
from telegram.constants import ParseMode

# Логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Змінні середовища
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("MEXC_API_KEY")
API_SECRET = os.getenv("MEXC_SECRET_KEY")

# Ініціалізація телеграм-бота
bot = Bot(token=BOT_TOKEN)

# Ініціалізація біржі
exchange = ccxt.mexc({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# Торгові налаштування
symbols = {
    "SOL/USDT:USDT": {"leverage": 300},
    "BTC/USDT:USDT": {"leverage": 500},
    "ETH/USDT:USDT": {"leverage": 500}
}
margin = 100

async def check_market():
    while True:
        try:
            for symbol, config in symbols.items():
                market = exchange.market(symbol)
                price_data = exchange.fetch_ticker(symbol)
                price = price_data['last']

                # Приклад стратегії: імпульсний вхід (можна вдосконалити)
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=5)
                close_prices = [c[4] for c in ohlcv]
                avg_price = sum(close_prices) / len(close_prices)

                signal = None
                if price > avg_price * 1.003:
                    signal = "LONG 🚀"
                elif price < avg_price * 0.997:
                    signal = "SHORT 🟥"

                if signal:
                    text = f"📈 <b>Новий сигнал: {signal}</b> на {symbol.split(':')[0]}
💰 Поточна ціна: <code>{price:.4f}</code>"
                    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode=ParseMode.HTML)

            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Помилка аналізу ринку: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(check_market())
