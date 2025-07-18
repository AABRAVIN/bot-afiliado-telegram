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
     def get_shopee_product_info_from_api(item_id, shop_id):
         print(f"Iniciando chamada de API para item: {item_id}, loja: {shop_id}")
         timestamp = int(time.time())
         path = "/api/v2/product/get_item_base_info"
         base_string = f"{SHOPEE_PARTNER_ID}{path}{timestamp}"
         sign = hmac.new(SHOPEE_SECRET_KEY.encode(), base_string.encode(), hashlib.sha256).hexdigest()
         url = "https://partner.shopee.com" + path
         params = {"partner_id": int(SHOPEE_PARTNER_ID), "timestamp": timestamp, "sign": sign, "shop_id": int(shop_id), "item_id_list": str(item_id)}
         try:
             response = requests.get(url, params=params, timeout=15)
             response.raise_for_status()
             data = response.json()
             if data.get("error"):
                 print(f"Erro retornado pela API da Shopee: {data.get('message')}")
                 return None
             print("Dados da API recebidos com sucesso.")
             return data['response']['item_list'][0]
         except Exception as e:
             print(f"ERRO na chamada de API: {e}")
             return None

     def extract_ids_from_url(url):
         print(f"Extraindo IDs da URL: {url}")
         try:
             headers = {'User-Agent': 'Mozilla/5.0'}
             response = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
             final_url = response.url
             print(f"URL final após redirecionamento: {final_url}")
             match = re.search(r"-i\.(\d+)\.(\d+)", final_url)
             if match:
                 shop_id, item_id = match.groups()
                 print(f"IDs encontrados: shop_id={shop_id}, item_id={item_id}")
                 return shop_id, item_id
             print("Não foi possível encontrar os IDs na URL.")
             return None, None
         except Exception as e:
             print(f"ERRO ao tentar resolver URL: {e}")
             return None, None

     bot = telebot.TeleBot(TELEGRAM_TOKEN)

     def criar_imagem_anuncio(imagem_produto_url, preco):
         try:
             print("Iniciando a criação da imagem...")
             fundo = Image.open("fundo.jpg").convert("RGBA"); logo = Image.open("logo.png").convert("RGBA")
             response = requests.get(imagem_produto_url, timeout=15); img_produto = Image.open(io.BytesIO(response.content)).convert("RGBA")
             tamanho_produto = int(fundo.width * 0.7); img_produto.thumbnail((tamanho_produto, tamanho_produto))
             tamanho_logo = int(fundo.width * 0.25); logo.thumbnail((tamanho_logo, tamanho_logo))
             pos_produto_x = (fundo.width - img_produto.width) // 2; pos_produto_y = (fundo.height - img_produto.height) // 2 - 50
             fundo.paste(img_produto, (pos_produto_x, pos_produto_y), img_produto)
             margem = 30; pos_logo_x = fundo.width - logo.width - margem; pos_logo_y = margem
             fundo.paste(logo, (pos_logo_x, pos_logo_y), logo)
             draw = ImageDraw.Draw(fundo)
             tamanho_fonte = int(fundo.width / 9); fonte = ImageFont.truetype("font.ttf", tamanho_fonte)
             texto_preco = f"R$ {preco:.2f}"; caixa_texto = draw.textbbox((0, 0), texto_preco, font=fonte)
             largura_texto = caixa_texto[2] - caixa_texto[0]; altura_texto = caixa_texto[3] - caixa_texto[1]
             pos_caixa_x = (fundo.width - largura_texto) // 2; pos_caixa_y = fundo.height - altura_texto - 80
             draw.rectangle((pos_caixa_x - 20, pos_caixa_y - 15, pos_caixa_x + largura_texto + 20, pos_caixa_y + altura_texto + 20), fill=(0, 0, 0, 128))
             draw.text((pos_caixa_x, pos_caixa_y), texto_preco, font=fonte, fill="white")
             final_image_stream = io.BytesIO()
             fundo.convert("RGB").save(final_image_stream, format='JPEG', quality=95)
             final_image_stream.seek(0)
             print("Criação de imagem concluída.")
             return final_image_stream
         except Exception as e:
             print(f"ERRO DENTRO DE criar_imagem_anuncio: {e}")
             return None

     @bot.message_handler(commands=['start', 'help'])
     def send_welcome(message):
         bot.reply_to(message, "Olá! Sou seu bot de anúncios via API (versão Render). Me envie um link de produto da Shopee.")

     @bot.message_handler(func=lambda message: 'shopee' in message.text)
     def handle_shopee_link(message):
         msg_espera = bot.reply_to(message, "🔍 Entendido. Processando link via API...")
         shop_id, item_id = extract_ids_from_url(message.text)
         if not shop_id or not item_id:
             bot.edit_message_text("❌ Não consegui identificar o produto a partir desse link.", msg_espera.chat.id, msg_espera.message_id)
             return
         product_info = get_shopee_product_info_from_api(item_id, shop_id)
         if not product_info:
             bot.edit_message_text("❌ Falha ao buscar dados na API. Verifique suas credenciais ou os logs.", msg_espera.chat.id, msg_espera.message_id)
             return
         titulo = product_info.get('item_name'); preco = product_info.get('price_info', [{}])[0].get('current_price'); imagem_id_list = product_info.get('image', {}).get('image_id_list', [])
         if not all([titulo, preco, imagem_id_list]):
              bot.edit_message_text("❌ A API retornou dados incompletos.", msg_espera.chat.id, msg_espera.message_id)
              return
         imagem_url = f"https://cf.shopee.com.br/file/{imagem_id_list[0]}"
         bot.edit_message_text("✅ Dados recebidos! Criando sua arte...", msg_espera.chat.id, msg_espera.message_id)
         imagem_final = criar_imagem_anuncio(imagem_url, float(preco))
         if imagem_final:
             legenda = f"*{titulo}*\n\n✅ Preço via API: *R$ {preco:.2f}*\n\n🔗 COMPRE AQUI:\n{message.text}"
             bot.send_photo(message.chat.id, photo=imagem_final, caption=legenda, parse_mode='Markdown')
         else:
             bot.send_message(message.chat.id, "❌ Desculpe, ocorreu um erro ao gerar a imagem.")
     
     print("Bot pronto e aguardando mensagens...")
     bot.infinity_polling()