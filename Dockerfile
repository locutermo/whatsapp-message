# Usar Python 3.10 versión ligera
FROM python:3.10-slim

# Instalar dependencias del sistema necesarias
# libmagic1 es necesario para detectar tipos de archivos (mencionado en tu README)
# ffmpeg suele ser útil para bots de whatsapp (audio/video)
RUN apt-get update && apt-get install -y \
    libmagic1 \
    ffmpeg \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto
EXPOSE 5000

# Comando para ejecutar el servidor (Modo Webhook)
CMD ["python", "webhook_server.py"]