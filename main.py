import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)
from flask import Flask
import threading

# Logging (opcional para debug)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Bot: comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Olá! Bot Shopee ativo com sucesso! 🛍️")

# Criação do aplicativo Flask (para manter o Render ativo)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Shopee está rodando!"

# Executar Flask em paralelo
def run_flask():
    app.run(host="0.0.0.0", port=10000)

# Inicializa o bot
async def main():
    application = ApplicationBuilder().token("8067364088:AAGdZQM16UncqNYE77DzHKqh9Kur8tr0-Hw").build()

    application.add_handler(CommandHandler("start", start))

    # Inicia o Flask em uma thread separada
    threading.Thread(target=run_flask).start()

    # Inicia o bot
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
