# Arquivo: bot.py (Versão API + Servidor Flask para Render)
import os
import threading
from flask import Flask

print("Script bot.py iniciado.")

# --- PARTE 1: SERVIDOR WEB PARA O RENDER ---
app = Flask(__name__)
@app.route('/')
def index():
    return "Servidor web no ar. Bot API em execução."

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

web_thread = threading.Thread(target=run_web_server)
web_thread.start()
print("Servidor web iniciado. Prosseguindo com a inicialização do bot...")

# --- PARTE 2: INICIALIZAÇÃO DO BOT E LÓGICA DA API ---
import json, requests, hmac, hashlib, time, re, telebot
from PIL import Image, ImageDraw, ImageFont
import io

try:
    with open("config.json") as f:
        config = json.load(f)
    TELEGRAM_TOKEN = config["telegram"]["token"]
    SHOPEE_PARTNER_ID = str(config["shopee"]["partner_id"])
    SHOPEE_SECRET_KEY = config["shopee"]["secret_key"]
    print("Configurações carregadas com sucesso.")
except Exception as e:
    print(f"ERRO CRÍTICO AO CARREGAR CONFIG.JSON: {e}")
    TELEGRAM_TOKEN = None

if TELEGRAM_TOKEN:
     # (O resto do código é exatamente o mesmo da versão API anterior)
     # Cole aqui todo o conteúdo restante, desde a definição da primeira função
     # da API Shopee até o final `bot.infinity_polling()`

     def get_shopee_product_info_from_api(item_id, shop_id):
         # ...
     
     def extract_ids_from_url(url):
         # ...
     
     bot = telebot.TeleBot(TELEGRAM_TOKEN)

     def criar_imagem_anuncio(imagem_produto_url, preco):
         # ...
     
     # ... e assim por diante, com todos os handlers e a chamada final
     print("Bot pronto e aguardando mensagens...")
     bot.infinity_polling()