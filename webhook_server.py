from flask import Flask, request, jsonify
from bot_whatsapp import get_bot_instance
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", ".")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
WHATSAPP_GROUP_JID = os.getenv("WHATSAPP_GROUP_JID", "")
PORT = int(os.getenv("PORT", 5000))

if DATA_DIR != "." and not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

JID_FILE = os.path.join(DATA_DIR, "active_group.jid")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

logger.info("🚀 Preparando bot de WhatsApp (inicialización diferida)...")
whatsapp_bot = None

def init_bot():
    global whatsapp_bot
    if whatsapp_bot is None:
        try:
            logger.info("🚀 Inicializando instancia del bot...")
            whatsapp_bot = get_bot_instance()
            logger.info("✅ Bot de WhatsApp iniciado correctamente")
        except Exception as e:
            logger.error(f"❌ Error al iniciar bot de WhatsApp: {e}")

# Inicializar bot antes de la primera petición si flask lo permite o de forma manual aquí con cuidado
try:
    init_bot()
except Exception as e:
    logger.error(f"⚠️ El servidor iniciará, pero el bot falló: {e}")


def format_jira_ticket_message(webhook_data):
    try:
        issue = webhook_data.get("issue", {})
        fields = issue.get("fields", {})

        key = issue.get("key", "N/A")
        summary = fields.get("summary") or "Sin título"
        description = fields.get("description") or "Sin descripción"

        reporter_obj = fields.get("reporter") or {}
        reporter = reporter_obj.get("displayName", "Desconocido")

        priority_obj = fields.get("priority") or {}
        priority = priority_obj.get("name", "Sin prioridad")

        issuetype_obj = fields.get("issuetype") or {}
        issue_type = issuetype_obj.get("name", "Ticket")

        created_str = fields.get("created", "")
        try:
            if created_str:
                created_dt = created_str.split(".")[0].replace("T", " ")
            else:
                created_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError, IndexError):
            created_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        jira_url = os.getenv("JIRA_URL", "https://integratelperu.atlassian.net")
        ticket_url = f"{jira_url}/browse/{key}"

        message = f"""🎫 *Nuevo Ticket en Jira*
        📋 *{issue_type}:* {key}
        📝 *Título:* {summary}
        👤 *Reportado por:* {reporter}
        ⚡ *Prioridad:* {priority}
        📄 *Descripción:*
        {description[:200]}{'...' if len(description) > 200 else ''}
        🔗 *Ver ticket:* {ticket_url}

        ⏰ *Creado:* {created_dt}
        """
        return message

    except Exception as e:
        logger.error(f"Error al formatear mensaje: {e}")
        return f"⚠️ Nuevo ticket creado en Jira (error al formatear detalles)\n{str(webhook_data)[:200]}"


@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint de health check"""
    bot_status = whatsapp_bot.is_connected if whatsapp_bot else False
    return jsonify(
        {
            "status": "ok",
            "bot_connected": bot_status,
            "bot_initialized": whatsapp_bot is not None,
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/webhook/jira", methods=["POST"])
def jira_webhook():
    if whatsapp_bot is None:
        return jsonify({"error": "Bot is not initialized. Please check server logs."}), 503

    try:
        webhook_data = request.json

        logger.info(f"📦 Payload recibido: {webhook_data}")

        if not webhook_data:
            return jsonify({"error": "No data provided"}), 400

        webhook_event = webhook_data.get("webhookEvent", "")

        logger.info(f"📨 Webhook recibido: {webhook_event}")

        if webhook_event == "jira:issue_created":
            message = format_jira_ticket_message(webhook_data)
            target_jid = None

            try:
                if os.path.exists(JID_FILE):
                    with open(JID_FILE, "r") as f:
                        file_jid = f.read().strip()
                        if file_jid:
                            target_jid = file_jid
                            logger.info(
                                f"📍 Usando JID dinámico desde archivo: {target_jid}"
                            )
            except Exception as e:
                logger.error(f"Error leyendo {JID_FILE}: {e}")

            if not target_jid:
                target_jid = WHATSAPP_GROUP_JID
                if target_jid:
                    logger.info(f"📄 Usando JID estático desde .env: {target_jid}")

            if not target_jid:
                logger.error(
                    "❌ No hay destino configurado. Añade el bot a un grupo o configura WHATSAPP_GROUP_JID"
                )
                return jsonify(
                    {
                        "error": "No WhatsApp group configured",
                        "message": "Add the bot to a group or set WHATSAPP_GROUP_JID in .env",
                    }
                ), 500

            success = whatsapp_bot.send_message(target_jid, message)

            if success:
                logger.info(
                    f"✅ Notificación enviada para ticket: {webhook_data.get('issue', {}).get('key', 'N/A')}"
                )
                return jsonify(
                    {"status": "success", "message": "Notification sent to WhatsApp"}
                ), 200
            else:
                logger.error("❌ Error al enviar mensaje a WhatsApp")
                return jsonify(
                    {"status": "error", "message": "Failed to send WhatsApp message"}
                ), 500
        else:
            # Evento no relevante, pero responder OK
            logger.info(f"ℹ️ Evento ignorado: {webhook_event}")
            return jsonify(
                {"status": "ignored", "message": f"Event {webhook_event} not processed"}
            ), 200

    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    logger.info(f"🌐 Servidor webhook iniciando en puerto {PORT}...")
    logger.info(f"📱 WhatsApp Group JID: {WHATSAPP_GROUP_JID or 'NO CONFIGURADO'}")
    logger.info(
        f"🔐 Webhook Secret: {'Configurado' if WEBHOOK_SECRET else 'NO CONFIGURADO (no recomendado)'}"
    )

    app.run(host="0.0.0.0", port=PORT, debug=False)
