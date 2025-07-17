# Use imagem oficial do Python
FROM python:3.13-slim

# Define diretório de trabalho no container
WORKDIR /app

# Copia os arquivos do projeto para o container
COPY . .

# Instala dependências
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Comando para iniciar o bot
CMD ["python", "main.py"]
