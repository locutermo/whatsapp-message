# Usar Python 3.10 versión ligera
FROM python:3.10-slim

# Evitar que los logs de Python se queden en el buffer (importante para ver logs en Zeabur)
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias
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

# Exponer el puerto predeterminado
EXPOSE 5000

# Comando para ejecutar el servidor
# Usamos main.py que tiene mejor manejo de la variable PORT de Zeabur
CMD ["python", "main.py"]