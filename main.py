
import os
import asyncio
import logging
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# MEXC API
api_key = os.getenv("MEXC_API_KEY")
secret = os.getenv("MEXC_SECRET_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

exchange = ccxt.mexc({
    'apiKey': api_key,
    'secret': secret,
    'options': {'defaultType': 'future'}
})

symbols = {
    'SOL/USDT:USDT': {'leverage': 300},
    'ETH/USDT:USDT': {'leverage': 500},
    'BTC/USDT:USDT': {'leverage': 500}
}

async def analyze_and_trade():
    while True:
        try:
            for symbol, data in symbols.items():
                market = exchange.market(symbol)
                bars = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
                df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['EMA20'] = df['close'].ewm(span=20).mean()
                df['EMA50'] = df['close'].ewm(span=50).mean()
                df['RSI'] = compute_rsi(df['close'], 14)
                signal = ''

                if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] and df['RSI'].iloc[-1] < 70:
                    signal = 'LONG'
                elif df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1] and df['RSI'].iloc[-1] > 30:
                    signal = 'SHORT'

                if signal:
                    entry_price = df['close'].iloc[-1]
                    stop_loss = round(entry_price * 0.997, 4) if signal == 'LONG' else round(entry_price * 1.003, 4)
                    take_profit = round(entry_price * 1.02, 4) if signal == 'LONG' else round(entry_price * 0.98, 4)
                    message = f"📈 Новий сигнал: <b>{signal}</b> на {symbol.split(':')[0]}
"                               f"🎯 Вхід: <b>{entry_price}</b>
"                               f"🛡️ SL: <b>{stop_loss}</b>
"                               f"💰 TP: <b>{take_profit}</b>
"                               f"📊 Леверидж: <b>{data['leverage']}x</b>

"                               f"⏱️ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.HTML)

        except Exception as e:
            logger.error(f"Помилка: {str(e)}")

        await asyncio.sleep(60)

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

if __name__ == '__main__':
    asyncio.run(analyze_and_trade())
