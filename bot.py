# Arquivo: bot.py (Versão Gerador de Imagens para Render)
import os
import threading
from flask import Flask
import telebot
import json
import requests
from PIL import Image, ImageDraw, ImageFont
import io

# --- PARTE 1: SERVIDOR WEB PARA O RENDER ---
app = Flask(__name__)
@app.route('/')
def index():
    return "Servidor do Bot Gerador de Imagens está no ar."

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

web_thread = threading.Thread(target=run_web_server)
web_thread.start()

# --- PARTE 2: INICIALIZAÇÃO DO BOT ---
try:
    with open("config.json") as f:
        config = json.load(f)
    TELEGRAM_TOKEN = config["telegram"]["token"]
except Exception as e:
    print(f"ERRO CRÍTICO AO LER CONFIG.JSON: {e}")
    TELEGRAM_TOKEN = None

if TELEGRAM_TOKEN:
    bot = telebot.TeleBot(TELEGRAM_TOKEN)

    # --- FUNÇÃO DE CRIAR IMAGEM (A mesma de antes) ---
    def criar_imagem_anuncio(imagem_produto_url, preco_texto):
        try:
            fundo = Image.open("fundo.jpg").convert("RGBA")
            logo = Image.open("logo.png").convert("RGBA")
            response = requests.get(imagem_produto_url, timeout=15)
            img_produto = Image.open(io.BytesIO(response.content)).convert("RGBA")
            
            tamanho_produto = int(fundo.width * 0.7); img_produto.thumbnail((tamanho_produto, tamanho_produto))
            tamanho_logo = int(fundo.width * 0.25); logo.thumbnail((tamanho_logo, tamanho_logo))

            pos_produto_x = (fundo.width - img_produto.width) // 2
            pos_produto_y = (fundo.height - img_produto.height) // 2 - 50
            fundo.paste(img_produto, (pos_produto_x, pos_produto_y), img_produto)
            margem = 30; pos_logo_x = fundo.width - logo.width - margem; pos_logo_y = margem
            fundo.paste(logo, (pos_logo_x, pos_logo_y), logo)

            draw = ImageDraw.Draw(fundo)
            tamanho_fonte = int(fundo.width / 9); fonte = ImageFont.truetype("font.ttf", tamanho_fonte)
            caixa_texto = draw.textbbox((0, 0), preco_texto, font=fonte)
            largura_texto = caixa_texto[2] - caixa_texto[0]; altura_texto = caixa_texto[3] - caixa_texto[1]
            pos_caixa_x = (fundo.width - largura_texto) // 2; pos_caixa_y = fundo.height - altura_texto - 80
            draw.rectangle((pos_caixa_x - 20, pos_caixa_y - 15, pos_caixa_x + largura_texto + 20, pos_caixa_y + altura_texto + 20), fill=(0, 0, 0, 128))
            draw.text((pos_caixa_x, pos_caixa_y), preco_texto, font=fonte, fill="white")

            final_image_stream = io.BytesIO()
            fundo.convert("RGB").save(final_image_stream, format='JPEG', quality=95)
            final_image_stream.seek(0)
            return final_image_stream
        except Exception as e:
            print(f"ERRO AO CRIAR IMAGEM: {e}")
            return None

    # --- NOVOS COMANDOS DO BOT ---
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        instrucoes = """
        Olá! Sou seu gerador de anúncios.

        Use o comando /anuncio com os dados separados por ponto e vírgula (;).

        *Formato:*
        `/anuncio URL_DA_IMAGEM.jpg; TÍTULO DO PRODUTO; R$ PREÇO; SEU_LINK_DE_AFILIADO`

        *Exemplo:*
        `/anuncio https://cf.shopee.com.br/file/exemplo.jpg; Super Cadeira Gamer; R$ 899,90; https://s.shopee.com.br/meulink`
        """
        bot.reply_to(message, instrucoes, parse_mode='Markdown')

    @bot.message_handler(commands=['anuncio'])
    def handle_anuncio(message):
        texto_comando = message.text.replace('/anuncio', '').strip()
        
        try:
            # Separa os dados usando o ponto e vírgula
            url_imagem, titulo, preco, link_afiliado = [parte.strip() for parte in texto_comando.split(';')]

            msg_espera = bot.reply_to(message, "✅ Dados recebidos! Gerando sua arte...")

            imagem_final = criar_imagem_anuncio(url_imagem, preco)

            if imagem_final:
                legenda = f"*{titulo}*\n\n✅ *{preco}*\n\n🔗 COMPRE AQUI:\n{link_afiliado}"
                bot.send_photo(message.chat.id, photo=imagem_final, caption=legenda, parse_mode='Markdown')
                bot.delete_message(msg_espera.chat.id, msg_espera.message_id)
            else:
                bot.edit_message_text("❌ Desculpe, ocorreu um erro ao gerar a imagem. Verifique a URL da imagem.", msg_espera.chat.id, msg_espera.message_id)

        except Exception as e:
            print(f"ERRO no comando /anuncio: {e}")
            bot.reply_to(message, "❌ Erro! Parece que você não enviou os dados no formato correto. Use /help para ver o exemplo.")

    print("Bot Gerador de Imagens pronto e aguardando comandos...")
    bot.infinity_polling()