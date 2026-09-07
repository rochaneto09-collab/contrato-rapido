FROM python:3.11-slim

# Instalar o LibreOffice e dependencias do sistema no container
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-script-provider-python \
    fontconfig \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar dependencias e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o codigo do projeto
COPY . .

# Porta padrão exposta pelo Render
EXPOSE 10000

# Executar a aplicação FastAPI
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]