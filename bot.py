# bot.py
import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:8000/webapp/")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message with a button to open mini app."""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hello {user.first_name}, welcome to Mini Burger House!\n\n"
        f"Click the button below to place your order 🍔",
        reply_markup=ReplyKeyboardMarkup(
            [
                [KeyboardButton("🍔 Open Burger Menu", web_app=WebAppInfo(url=WEBAPP_URL))]
            ],
            resize_keyboard=True
        )
    )

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN not set")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
