# Arquivo: bot.py (Versão final com depuração)
import os
import threading
from flask import Flask

print("Script bot.py iniciado.")

# --- PARTE 1: O SERVIDOR WEB ---
app = Flask(__name__)

@app.route('/')
def index():
    return "Servidor web no ar. Bot em execução."

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

web_thread = threading.Thread(target=run_web_server)
web_thread.start()
print("Servidor web iniciado em thread. Prosseguindo com a inicialização do bot...")

# --- PARTE 2: INICIALIZAÇÃO DO BOT ---
import telebot
import json
import requests
from bs4 import BeautifulSoup
import re
from PIL import Image, ImageDraw, ImageFont
import io

# --- Carregando Token ---
print("Tentando carregar o token do config.json...")
try:
    with open("config.json") as f:
        config = json.load(f)
    TELEGRAM_TOKEN = config["telegram"]["token"]
    if not TELEGRAM_TOKEN or len(TELEGRAM_TOKEN.split(':')) != 2:
        print("ERRO: O token carregado do config.json parece ser inválido ou está vazio.")
        TELEGRAM_TOKEN = None
    else:
        print("Token carregado com sucesso!")
except Exception as e:
    print(f"ERRO CRÍTICO AO LER config.json: {e}")
    TELEGRAM_TOKEN = None

# Só continua se o token foi carregado corretamente
if TELEGRAM_TOKEN:
    print("Inicializando o objeto 'bot' do TeleBot...")
    bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode='Markdown')
    print("Objeto 'bot' inicializado.")

    # --- Funções do Bot (sem mudanças) ---
    def criar_imagem_anuncio(imagem_produto_url, preco, caminho_fundo="fundo.jpg", caminho_logo="logo.png", caminho_fonte="font.ttf"):
        try:
            # (código da função sem alterações)
            fundo = Image.open(caminho_fundo).convert("RGBA")
            logo = Image.open(caminho_logo).convert("RGBA")
            response = requests.get(imagem_produto_url)
            img_produto = Image.open(io.BytesIO(response.content)).convert("RGBA")
            tamanho_produto = int(fundo.width * 0.7)
            img_produto.thumbnail((tamanho_produto, tamanho_produto))
            tamanho_logo = int(fundo.width * 0.25)
            logo.thumbnail((tamanho_logo, tamanho_logo))
            pos_produto_x = (fundo.width - img_produto.width) // 2
            pos_produto_y = (fundo.height - img_produto.height) // 2 - 50
            fundo.paste(img_produto, (pos_produto_x, pos_produto_y), img_produto)
            margem = 30
            pos_logo_x = fundo.width - logo.width - margem
            pos_logo_y = margem
            fundo.paste(logo, (pos_logo_x, pos_logo_y), logo)
            draw = ImageDraw.Draw(fundo)
            tamanho_fonte = int(fundo.width / 9)
            fonte = ImageFont.truetype(caminho_fonte, tamanho_fonte)
            texto_preco = f"R$ {preco}"
            caixa_texto = draw.textbbox((0, 0), texto_preco, font=fonte)
            largura_texto = caixa_texto[2] - caixa_texto[0]
            altura_texto = caixa_texto[3] - caixa_texto[1]
            pos_caixa_x = (fundo.width - largura_texto) // 2
            pos_caixa_y = fundo.height - altura_texto - 80
            draw.rectangle((pos_caixa_x - 20, pos_caixa_y - 15, pos_caixa_x + largura_texto + 20, pos_caixa_y + altura_texto + 20), fill=(0, 0, 0, 128))
            draw.text((pos_caixa_x, pos_caixa_y), texto_preco, font=fonte, fill="white")
            final_image_stream = io.BytesIO()
            fundo.convert("RGB").save(final_image_stream, format='JPEG', quality=95)
            final_image_stream.seek(0)
            return final_image_stream
        except Exception as e:
            print(f"ERRO DENTRO DE criar_imagem_anuncio: {e}")
            return None

    def extrair_dados_shopee(url):
        # (código da função sem alterações)
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            imagem_url = soup.find('meta', property='og:image')['content']
            titulo = soup.find('meta', property='og:title')['content']
            preco_div = soup.find('div', class_='flex items-center _90fTvx')
            preco_bruto = preco_div.text if preco_div and preco_div.text else soup.find(string=re.compile(r'R\$\s?[\d,.]+')).strip()
            match = re.search(r'[\d,.]+', preco_bruto.replace('.', ''))
            preco = match.group(0).replace(',', '.') if match else "N/D"
            return {"titulo": titulo, "preco": preco, "imagem_url": imagem_url}
        except Exception as e:
            print(f"ERRO DENTRO DE extrair_dados_shopee: {e}")
            return None

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        print("Comando /start recebido. Respondendo...")
        bot.reply_to(message, "👋 Olá! Sou seu designer de posts. Me envie um link de afiliado da Shopee e eu criarei um anúncio personalizado!")

    @bot.message_handler(func=lambda message: re.search(r'shopee\.com', message.text))
    def criar_post_afiliado(message):
        print(f"Link da Shopee recebido: {message.text}")
        # (código da função sem alterações)
        link_original = message.text
        msg_espera = bot.reply_to(message, "🎨 Recebido! Preparando sua arte personalizada...")
        dados_produto = extrair_dados_shopee(link_original)
        if dados_produto:
            imagem_final = criar_imagem_anuncio(dados_produto['imagem_url'], dados_produto['preco'])
            bot.delete_message(chat_id=msg_espera.chat.id, message_id=msg_espera.message_id)
            if imagem_final:
                legenda = f"{dados_produto['titulo']}\n\n🔗 *COMPRE AQUI:*\n{link_original}\n\n_Preço e estoque podem variar!_"
                bot.send_photo(message.chat.id, photo=imagem_final, caption=legenda)
            else:
                bot.reply_to(message, "❌ Desculpe, não consegui gerar a imagem personalizada.")
        else:
            bot.delete_message(chat_id=msg_espera.chat.id, message_id=msg_espera.message_id)
            bot.reply_to(message, "❌ Desculpe, não consegui extrair as informações do link.")

    print("Tudo pronto. Chamando bot.infinity_polling() para iniciar o recebimento de mensagens...")
    bot.infinity_polling()

else:
    print("FINALIZANDO: Bot não foi iniciado devido à falta de um token válido.")