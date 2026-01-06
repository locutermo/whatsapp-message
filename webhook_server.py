from flask import Flask, request, jsonify
from bot_whatsapp import get_bot_instance
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import qrcode
import io
import base64

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

logger.info("🚀 Iniciando bot de WhatsApp...")
whatsapp_bot = get_bot_instance()
logger.info("✅ Bot de WhatsApp iniciado")


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
    return jsonify(
        {
            "status": "ok",
            "bot_connected": whatsapp_bot.is_connected,
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/qr", methods=["GET"])
def get_qr():
    """Endpoint para mostrar el código QR de WhatsApp con auto-update"""
    if whatsapp_bot.is_connected:
        return (
            """
        <html>
            <head><title>Bot Conectado</title><style>body{font-family:sans-serif;text-align:center;padding-top:50px;}</style></head>
            <body>
                <h1>✅ Bot ya está conectado a WhatsApp</h1>
                <p>El bot está listo para procesar notificaciones de Jira.</p>
            </body>
        </html>
        """,
            200,
        )

    if not whatsapp_bot.qr_data:
        return (
            """
        <html>
            <head>
                <title>Generando QR...</title>
                <meta http-equiv="refresh" content="5">
                <style>body{font-family:sans-serif;text-align:center;padding-top:50px;}</style>
            </head>
            <body>
                <h1>⏳ Generando código QR...</h1>
                <p>Por favor espera un momento, la página se recargará automáticamente cada 5 segundos.</p>
            </body>
        </html>
        """,
            200,
        )

    # Generar imagen QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(whatsapp_bot.qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Guardar en buffer de memoria y convertir a base64
    img_io = io.BytesIO()
    img.save(img_io, "PNG")
    img_io.seek(0)
    img_base64 = base64.b64encode(img_io.getvalue()).decode()

    return (
        f"""
    <html>
        <head>
            <title>Vincular WhatsApp</title>
            <meta http-equiv="refresh" content="15">
            <style>
                body {{ font-family: sans-serif; text-align: center; padding: 20px; background-color: #f0f2f5; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                img {{ margin: 20px 0; }}
                .status {{ color: #65676b; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Escanea el código QR</h1>
                <p>Abre WhatsApp en tu teléfono > Dispositivos vinculados > Vincular un dispositivo</p>
                <img src="data:image/png;base64,{img_base64}" alt="QR WhatsApp" />
                <p class="status">La página se actualiza automáticamente cada 15 segundos.</p>
                <p class="status">Última actualización: {datetime.now().strftime('%H:%M:%S')}</p>
            </div>
        </body>
    </html>
    """,
        200,
    )


@app.route("/webhook/jira", methods=["POST"])
def jira_webhook():
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
