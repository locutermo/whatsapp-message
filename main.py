import os
import logging
from webhook_server import app, PORT

if __name__ == "__main__":
    # Zeabur y otros PaaS suelen inyectar PORT
    # webhook_server ya lo maneja, pero por si acaso lo reforzamos aquí
    port = int(os.environ.get("PORT", PORT))
    
    logging.info(f"🚀 Iniciando servidor desde main.py en puerto {port}...")
    app.run(host="0.0.0.0", port=port)
