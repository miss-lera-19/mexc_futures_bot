import logging
import os
import ccxt
import pandas as pd
import ta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

exchange = ccxt.mexc({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'options': {'defaultType': 'future'},
    'enableRateLimit': True,
})

symbols = ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT"]

def analyze_symbol(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        df['ema_fast'] = ta.trend.ema_indicator(df['close'], window=5)
        df['ema_slow'] = ta.trend.ema_indicator(df['close'], window=20)
        df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()

        last = df.iloc[-1]
        direction = None

        if last['rsi'] < 30 and last['ema_fast'] > last['ema_slow']:
            direction = "LONG"
        elif last['rsi'] > 70 and last['ema_fast'] < last['ema_slow']:
            direction = "SHORT"

        if direction:
            entry = last['close']
            atr = last['atr']
            sl = round(entry - atr * 0.5, 2) if direction == "LONG" else round(entry + atr * 0.5, 2)
            tp = round(entry + atr * 2, 2) if direction == "LONG" else round(entry - atr * 2, 2)
            return {
                "symbol": symbol.split(":")[0],
                "direction": direction,
                "entry": round(entry, 2),
                "sl": sl,
                "tp": tp
            }
        return None
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📉 Отримати сигнал", callback_data='signal')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ Бот запущено.
Натисни кнопку, щоб отримати сигнал або зачекай автоматичне оновлення.", reply_markup=reply_markup)
    context.job_queue.run_repeating(send_signals, interval=60, first=5, chat_id=update.effective_chat.id)

async def send_signals(context: ContextTypes.DEFAULT_TYPE):
    messages = []
    for symbol in symbols:
        signal = analyze_symbol(symbol)
        if signal:
            msg = f"💹 Сигнал по {signal['symbol']}:
➡️ {signal['direction']}
💰 Entry: {signal['entry']}
❌ SL: {signal['sl']}
✅ TP: {signal['tp']}"
            messages.append(msg)
    if messages:
        await context.bot.send_message(chat_id=context.job.chat_id, text="\n\n".join(messages))

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()