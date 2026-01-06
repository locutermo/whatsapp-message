import os
import logging

# Salida inmediata para depuración en Zeabur
print("🚀 [Bootstrap] Iniciando contenedor principal...")
logging.basicConfig(level=logging.INFO)

from webhook_server import app, PORT

if __name__ == "__main__":
    port = int(os.environ.get("PORT", PORT))

    logging.info(f"🚀 Iniciando servidor desde main.py en puerto {port}...")
    app.run(host="0.0.0.0", port=port)
