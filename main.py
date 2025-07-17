from flask import Flask, request
import telegram
import os

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telegram.Bot(token=TOKEN)

@app.route(f"/{TOKEN}", methods=["POST"])
def respond():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    text = update.message.text

    if text.startswith("http"):
        bot.send_message(chat_id=chat_id, text=f"🔗 Link recebido: {text}")
        # Aqui será onde buscamos Shopee e geramos imagem futuramente
    else:
        bot.send_message(chat_id=chat_id, text="Envie um link da Shopee")

    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "✅ Bot Shopee está online"

if __name__ == "__main__":
    app.run()
