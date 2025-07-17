import logging
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from bs4 import BeautifulSoup
import re

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8067364088:AAGdZQM16UncqNYE77DzHKqh9Kur8tr0-Hw"

def pegar_dados_shopee(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception("Não foi possível acessar a página")

    soup = BeautifulSoup(response.text, "html.parser")

    titulo = soup.find("title").text.strip()

    preco = None
    imagem = None
    for script in soup.find_all("script"):
        if script.string and '"price"' in script.string:
            preco_match = re.search(r'"price":(\d+)', script.string)
            if preco_match:
                preco = int(preco_match.group(1)) / 100000
            img_match = re.search(r'"image":"(https:[^"]+)"', script.string)
            if img_match:
                imagem = img_match.group(1)
            break

    if preco is None:
        preco = "Indisponível"
    else:
        preco = f"{preco:.2f}".replace(".", ",")

    if imagem is None:
        imagem = "https://cf.shopee.com.br/file/default_product_image.png"

    return titulo, preco, imagem

def gerar_imagem_anuncio(titulo, preco, url_imagem_produto, caminho_logo, caminho_saida):
    try:
        response = requests.get(url_imagem_produto)
        img_produto = Image.open(BytesIO(response.content)).convert("RGBA")

        largura, altura = 800, 1000
        fundo = Image.new("RGBA", (largura, altura), "white")

        img_produto.thumbnail((760, 600))
        pos_x = (largura - img_produto.width) // 2
        fundo.paste(img_produto, (pos_x, 100), img_produto)

        draw = ImageDraw.Draw(fundo)
        # Usa fontes padrão (compatível com Render)
        fonte_titulo = ImageFont.load_default()
        fonte_preco = ImageFont.load_default()

        linhas = []
        palavras = titulo.split()
        linha_atual = ""
        for palavra in palavras:
            largura_linha, _ = draw.textsize(linha_atual + " " + palavra, font=fonte_titulo)
            if largura_linha < 760:
                linha_atual += " " + palavra
            else:
                linhas.append(linha_atual.strip())
                linha_atual = palavra
        linhas.append(linha_atual.strip())

        y_texto = 720
        for linha in linhas:
            draw.text((20, y_texto), linha, font=fonte_titulo, fill="black")
            y_texto += 20

        draw.text((20, y_texto + 20), f"✅️ A partir de: R$ {preco}", font=fonte_preco, fill="red")

        try:
            logo = Image.open(caminho_logo).convert("RGBA")
            logo.thumbnail((120, 120))
            pos_logo = (largura - logo.width - 20, 20)
            fundo.paste(logo, pos_logo, logo)
        except Exception as e:
            print("Erro ao carregar logo:", e)

        fundo.convert("RGB").save(caminho_saida, "JPEG", quality=85)
        return True
    except Exception as e:
        print("Erro ao gerar imagem:", e)
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Envie um link da Shopee e eu criarei um anúncio com sua logo."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    if "shopee.com.br" not in texto:
        await update.message.reply_text("Por favor, envie um link válido da Shopee.")
        return

    await update.message.reply_text("Recebi seu link! Gerando anúncio...")

    try:
        titulo, preco, url_imagem = pegar_dados_shopee(texto)
    except Exception as e:
        await update.message.reply_text(f"Erro ao acessar o produto: {e}")
        return

    caminho_logo = "logo.png"
    caminho_saida = "anuncio.jpg"

    sucesso = gerar_imagem_anuncio(titulo, preco, url_imagem, caminho_logo, caminho_saida)
    if not sucesso:
        await update.message.reply_text("Erro ao gerar a imagem do anúncio.")
        return

    legenda = (
        f"{titulo}\n\n"
        f"✅️ A partir de: R$ {preco}\n\n"
        f"🔗 COMPRE AQUI: {texto}\n\n"
        f"⚠️ Sujeito a variação de preço e disponibilidade no site.\n\n"
        f"📍Descubra ofertas impermeáveis!\n👉 https://collshp.com/tanofaro"
    )

    with open(caminho_saida, "rb") as foto:
        await update.message.reply_photo(photo=foto, caption=legenda)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot iniciado...")
    app.run_polling()

