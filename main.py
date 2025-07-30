import asyncio
import logging
import pandas as pd
import ccxt
import ta
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BOT_TOKEN = os.getenv("BOT_TOKEN")

SYMBOLS = ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT"]

exchange = ccxt.mexc({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'options': {'defaultType': 'future'}
})

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def analyze_market(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
        df = pd.DataFrame(ohlcv, columns=["time", "open", "high", "low", "close", "volume"])
        df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
        df["ema_fast"] = ta.trend.EMAIndicator(df["close"], window=9).ema_indicator()
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

        return f"📈 Signal for {symbol.split(':')[0]}:
Direction: {direction}
Entry: {entry}
SL: {sl}
TP: {tp}"

    except Exception as e:
        return f"⚠️ Error analyzing {symbol}: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот активний")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = []
    for symbol in SYMBOLS:
        signal_msg = analyze_market(symbol)
        if signal_msg:
            messages.append(signal_msg)

    if messages:
        for msg in messages:
            await update.message.reply_text(msg)
    else:
        await update.message.reply_text("📊 Наразі немає сигналів.")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())