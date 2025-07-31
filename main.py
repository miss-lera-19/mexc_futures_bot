import os
import asyncio
import logging
import ccxt
import pandas as pd
import numpy as np
from telegram import Bot
from datetime import datetime
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from dotenv import load_dotenv

load_dotenv()

# ENV variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("MEXC_API_KEY")
API_SECRET = os.getenv("MEXC_SECRET_KEY")

bot = Bot(token=BOT_TOKEN)

# Логування
logging.basicConfig(level=logging.INFO)

# Параметри
symbols = ['SOL/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT']
leverage_map = {
    'SOL/USDT:USDT': 300,
    'BTC/USDT:USDT': 500,
    'ETH/USDT:USDT': 500
}
margin = 100

exchange = ccxt.mexc({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})


async def analyze_market():
    while True:
        for symbol in symbols:
            try:
                market_data = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
                df = pd.DataFrame(market_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['EMA20'] = EMAIndicator(df['close'], window=20).ema_indicator()
                df['EMA50'] = EMAIndicator(df['close'], window=50).ema_indicator()
                df['RSI'] = RSIIndicator(df['close'], window=14).rsi()
                macd = MACD(df['close'])
                df['MACD'] = macd.macd()
                df['Signal'] = macd.macd_signal()

                latest = df.iloc[-1]
                price = latest['close']

                long_signal = (
                    latest['EMA20'] > latest['EMA50'] and
                    latest['MACD'] > latest['Signal'] and
                    latest['RSI'] < 70
                )
                short_signal = (
                    latest['EMA20'] < latest['EMA50'] and
                    latest['MACD'] < latest['Signal'] and
                    latest['RSI'] > 30
                )

                direction = None
                if long_signal:
                    direction = 'LONG 🔼'
                elif short_signal:
                    direction = 'SHORT 🔽'

                if direction:
                    leverage = leverage_map[symbol]
                    entry_price = round(price, 4)
                    take_profit = round(entry_price * (1.01 if direction == 'LONG 🔼' else 0.99), 4)
                    stop_loss = round(entry_price * (0.99 if direction == 'LONG 🔼' else 1.01), 4)

                    text = (
                        f"📈 <b>Новий сигнал:</b>\n"
                        f"Монета: <b>{symbol.split('/')[0]}</b>\n"
                        f"Напрямок: <b>{direction}</b>\n"
                        f"Ціна входу: <b>{entry_price}</b>\n"
                        f"Take Profit: <b>{take_profit}</b>\n"
                        f"Stop Loss: <b>{stop_loss}</b>\n"
                        f"Плече: <b>{leverage}x</b>\n"
                        f"Маржа: <b>{margin}$</b>\n"
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')
                    logging.info(f"Signal sent for {symbol}: {direction}")

            except Exception as e:
                logging.error(f"Error analyzing {symbol}: {e}")

        await asyncio.sleep(60)


if __name__ == '__main__':
    asyncio.run(analyze_market())
