import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from config import API_KEY, API_SECRET, BOT_TOKEN
import ccxt.async_support as ccxt
import ta
import pandas as pd
import datetime

# Логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Ініціалізація біржі
exchange = ccxt.mexc({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'options': {'defaultType': 'future'}
})

SYMBOLS = ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT"]

async def analyze_market(symbol):
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
        df = pd.DataFrame(ohlcv, columns=["time", "open", "high", "low", "close", "volume"])
        df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
        df["ema_fast"] = ta.trend.EMAIndicator(df["close"], window=5).ema_indicator()
        df["ema_slow"] = ta.trend.EMAIndicator(df["close"], window=21).ema_indicator()

        last = df.iloc[-1]

        if last["rsi"] < 30 and last["ema_fast"] > last["ema_slow"]:
            direction = "LONG"
        elif last["rsi"] > 70 and last["ema_fast"] < last["ema_slow"]:
            direction = "SHORT"
        else:
            return None

        entry = last["close"]
        sl = round(entry * 0.99, 2) if direction == "LONG" else round(entry * 1.01, 2)
        tp = round(entry * 1.02, 2) if direction == "LONG" else round(entry * 0.98, 2)

        return f"🔔 Signal for {symbol.split('/')[0]}:
➡️ {direction}
💰 Entry: {entry}
🛡 SL: {sl}
🎯 TP: {tp}"
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None

async def check_market():
    for symbol in SYMBOLS:
        signal = await analyze_market(symbol)
        if signal:
            await bot.send_message(chat_id="@my_mexc_futures_bot", text=signal)

async def scheduler():
    while True:
        await check_market()
        await asyncio.sleep(60)

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущено. Очікую на сигнали...")

async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())