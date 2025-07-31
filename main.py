import os
import time
import ccxt
import asyncio
import logging
import pandas as pd
import ta
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
chat_id = os.getenv("CHAT_ID")

exchange = ccxt.mexc({
    'apiKey': os.getenv("MEXC_API_KEY"),
    'secret': os.getenv("MEXC_SECRET_KEY"),
    'options': {'defaultType': 'future'}
})

symbols = {
    'BTC/USDT': 500,
    'ETH/USDT': 500,
    'SOL/USDT': 300
}

position_open = {}

def fetch_ohlcv(symbol):
    bars = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=50)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['ema'] = ta.trend.EMAIndicator(df['close'], window=14).ema_indicator()
    return df

def generate_signal(df):
    if df['close'].iloc[-1] > df['ema'].iloc[-1] and df['rsi'].iloc[-1] < 70:
        return "LONG"
    elif df['close'].iloc[-1] < df['ema'].iloc[-1] and df['rsi'].iloc[-1] > 30:
        return "SHORT"
    else:
        return None

def calculate_tp_sl(entry_price, signal, leverage):
    profit_target = 0.01  # 1%
    sl_buffer = 0.003     # 0.3%
    tp = round(entry_price * (1 + profit_target * leverage), 4) if signal == "LONG" else round(entry_price * (1 - profit_target * leverage), 4)
    sl = round(entry_price * (1 - sl_buffer * leverage), 4) if signal == "LONG" else round(entry_price * (1 + sl_buffer * leverage), 4)
    return tp, sl

def open_position(symbol, signal, leverage):
    market = exchange.market(symbol)
    price = exchange.fetch_ticker(symbol)['last']
    margin = 100
    quantity = round((margin * leverage) / price, 3)

    exchange.set_leverage(leverage, symbol)
    side = 'buy' if signal == 'LONG' else 'sell'

    order = exchange.create_market_order(symbol, side, quantity)
    tp, sl = calculate_tp_sl(price, signal, leverage)

    position_open[symbol] = {
        'side': side,
        'entry': price,
        'tp': tp,
        'sl': sl
    }

    return f"📈 Новий сигнал: <b>{signal}</b> на {symbol.split(':')[0]}\n💰 Вхід: {price}\n🎯 TP: {tp}\n🛡 SL: {sl}"

async def check_market():
    while True:
        try:
            for symbol, leverage in symbols.items():
                df = fetch_ohlcv(symbol)
                signal = generate_signal(df)

                if signal and symbol not in position_open:
                    message = open_position(symbol, signal, leverage)
                    await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')

        except Exception as e:
            logging.error(f"Помилка: {str(e)}")

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(check_market())
