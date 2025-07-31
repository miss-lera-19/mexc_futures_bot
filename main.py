import os
import asyncio
import logging
import ccxt
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("MEXC_API_KEY")
API_SECRET = os.getenv("MEXC_SECRET_KEY")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)
logging.basicConfig(level=logging.INFO)

exchange = ccxt.mexc({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

async def start(update, context):
    await update.message.reply_text("✅ Бот активний та працює у фоні!")

async def check_market_and_send_signal():
    while True:
        try:
            symbols = ["SOL/USDT:USDT", "BTC/USDT:USDT", "ETH/USDT:USDT"]
            for symbol in symbols:
                ticker = exchange.fetch_ticker(symbol)
                price = ticker["last"]
                signal = generate_signal(symbol, price)
                if signal:
                    await bot.send_message(chat_id=CHAT_ID, text=signal)
        except Exception as e:
            logging.error(f"❌ Error checking market: {e}")
        await asyncio.sleep(60)

def generate_signal(symbol, price):
    entry = round(price, 4)
    if "BTC" in symbol or "ETH" in symbol:
        tp = round(entry * 1.0025, 4)
        sl = round(entry * 0.9975, 4)
        direction = "LONG"
    else:
        tp = round(entry * 0.9975, 4)
        sl = round(entry * 1.0025, 4)
        direction = "SHORT"
    return f"📊 Торговий сигнал для {symbol.split(':')[0]}
📈 Тип: {direction}
💰 Ціна входу: {entry}
🎯 Take Profit: {tp}
🛑 Stop Loss: {sl}"

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    await app.start()
    await bot.send_message(chat_id=CHAT_ID, text="✅ Бот запущено та аналізує ринок.")
    await check_market_and_send_signal()

if __name__ == "__main__":
    asyncio.run(main())
