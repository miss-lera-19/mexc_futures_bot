import os
import time
import ccxt
import logging
import asyncio
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from telegram import Bot

# Логування
logging.basicConfig(level=logging.INFO)

# Змінні середовища
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_KEY = os.getenv('MEXC_API_KEY')
API_SECRET = os.getenv('MEXC_SECRET_KEY')

bot = Bot(token=BOT_TOKEN)

# Параметри
symbols = ['SOL/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT']
leverage_map = {'SOL/USDT:USDT': 300, 'BTC/USDT:USDT': 500, 'ETH/USDT:USDT': 500}
amount = 100

# Ініціалізація біржі
exchange = ccxt.mexc({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'options': {'defaultType': 'future'},
    'enableRateLimit': True
})

# Встановлення кредитного плеча
def set_leverage(symbol):
    market = exchange.market(symbol)
    try:
        exchange.set_leverage(leverage_map[symbol], market['id'], {'marginMode': 'isolated'})
    except Exception as e:
        logging.warning(f"Не вдалося встановити плече для {symbol}: {e}")

# Отримання даних та аналіз
def analyze(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['ema'] = EMAIndicator(close=df['close'], window=20).ema_indicator()
    df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()

    last_candle = df.iloc[-1]
    prev_candle = df.iloc[-2]

    if last_candle['close'] > last_candle['ema'] and last_candle['rsi'] > 55 and prev_candle['rsi'] < 55:
        return "LONG", last_candle['close']
    elif last_candle['close'] < last_candle['ema'] and last_candle['rsi'] < 45 and prev_candle['rsi'] > 45:
        return "SHORT", last_candle['close']
    else:
        return None, None

# Торгівля
def place_order(symbol, side, price):
    market = exchange.market(symbol)
    set_leverage(symbol)

    order_side = 'buy' if side == 'LONG' else 'sell'
    sl = price * (0.985 if side == 'LONG' else 1.015)
    tp = price * (1.03 if side == 'LONG' else 0.97)

    try:
        exchange.create_order(
            symbol=symbol,
            type='market',
            side=order_side,
            amount=amount / price,
            params={
                'stopLossPrice': round(sl, 4),
                'takeProfitPrice': round(tp, 4)
            }
        )
        return True
    except Exception as e:
        logging.error(f"Помилка при створенні ордера: {e}")
        return False

# Основна логіка
async def run_bot():
    while True:
        for symbol in symbols:
            signal, price = analyze(symbol)
            if signal:
                opened = place_order(symbol, signal, price)
                if opened:
                    message = f"📈 Новий сигнал: <b>{signal}</b> на {symbol.split(':')[0]}\n🎯 Ціна входу: {price:.2f}"
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_bot())
