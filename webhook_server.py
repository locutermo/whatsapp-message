"""
Servidor webhook para recibir notificaciones de Jira
y enviarlas a WhatsApp
"""
from flask import Flask, request, jsonify
from bot_whatsapp import get_bot_instance
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', '')
WHATSAPP_GROUP_JID = os.getenv('WHATSAPP_GROUP_JID', '')
PORT = int(os.getenv('PORT', 5000))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)

# Inicializar bot de WhatsApp
logger.info("🚀 Iniciando bot de WhatsApp...")
whatsapp_bot = get_bot_instance()
logger.info("✅ Bot de WhatsApp iniciado")

def format_jira_ticket_message(webhook_data):
    """
    Formatea los datos del webhook de Jira en un mensaje legible
    
    Args:
        webhook_data: Datos del webhook de Jira
        
    Returns:
        str: Mensaje formateado para WhatsApp
    """
    try:
        issue = webhook_data.get('issue', {})
        fields = issue.get('fields', {})
        
        # Extraer información relevante
        key = issue.get('key', 'N/A')
        summary = fields.get('summary') or 'Sin título'
        description = fields.get('description') or 'Sin descripción'
        
        reporter_obj = fields.get('reporter') or {}
        reporter = reporter_obj.get('displayName', 'Desconocido')
        
        priority_obj = fields.get('priority') or {}
        priority = priority_obj.get('name', 'Sin prioridad')
        
        issuetype_obj = fields.get('issuetype') or {}
        issue_type = issuetype_obj.get('name', 'Ticket')
        
        # Obtener fecha real de creación del ticket
        created_str = fields.get('created', '')
        try:
            # Intentar formatear la fecha de Jira (ej: 2026-01-05T07:26:06.000+0000)
            if created_str:
                # Simplificación para mostrar fecha legible sin dependencias extra
                created_dt = created_str.split('.')[0].replace('T', ' ')
            else:
                created_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except:
            created_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Construir URL del ticket
        jira_url = os.getenv('JIRA_URL', 'https://integratelperu.atlassian.net')
        ticket_url = f"{jira_url}/browse/{key}"
        
        # Formatear mensaje
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

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        'status': 'ok',
        'bot_connected': whatsapp_bot.is_connected,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/webhook/jira', methods=['POST'])
def jira_webhook():
    """
    Endpoint para recibir webhooks de Jira
    """
    try:
        # Log de headers para debug
        # logger.info(f"📨 Headers recibidos: {dict(request.headers)}")

        # Verificar secret si está configurado
        # if WEBHOOK_SECRET:
        #     provided_secret = request.headers.get('X-Webhook-Secret', '')
        #     if provided_secret != WEBHOOK_SECRET:
        #         logger.warning("⚠️ Intento de acceso con secret inválido")
        #         return jsonify({'error': 'Unauthorized'}), 401
        
        # Obtener datos del webhook
        webhook_data = request.json
        
        logger.info(f"📦 Payload recibido: {webhook_data}")
        
        if not webhook_data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Verificar que sea un evento de creación de issue
        webhook_event = webhook_data.get('webhookEvent', '')
        
        logger.info(f"📨 Webhook recibido: {webhook_event}")
        
        # Solo procesar eventos de creación de issues
        if webhook_event == 'jira:issue_created':
            # Formatear mensaje
            message = format_jira_ticket_message(webhook_data)
            
            # Verificar que tengamos el JID del grupo configurado
            # Prioridad 1: Archivo generado dinámicamente (por comando /group o autojoin)
            # Prioridad 2: Variable de entorno (fallback estático)
            target_jid = None
            
            try:
                if os.path.exists("active_group.jid"):
                    with open("active_group.jid", "r") as f:
                        file_jid = f.read().strip()
                        if file_jid:
                            target_jid = file_jid
                            logger.info(f"📍 Usando JID dinámico desde archivo: {target_jid}")
            except Exception as e:
                logger.error(f"Error leyendo active_group.jid: {e}")
            
            # Si no hay JID en archivo, usar variable de entorno
            if not target_jid:
                target_jid = WHATSAPP_GROUP_JID
                if target_jid:
                    logger.info(f"📄 Usando JID estático desde .env: {target_jid}")

            if not target_jid:
                logger.error("❌ No hay destino configurado. Añade el bot a un grupo o configura WHATSAPP_GROUP_JID")
                return jsonify({
                    'error': 'No WhatsApp group configured',
                    'message': 'Add the bot to a group or set WHATSAPP_GROUP_JID in .env'
                }), 500
            
            # Enviar mensaje a WhatsApp
            success = whatsapp_bot.send_message(target_jid, message)
            
            if success:
                logger.info(f"✅ Notificación enviada para ticket: {webhook_data.get('issue', {}).get('key', 'N/A')}")
                return jsonify({
                    'status': 'success',
                    'message': 'Notification sent to WhatsApp'
                }), 200
            else:
                logger.error("❌ Error al enviar mensaje a WhatsApp")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to send WhatsApp message'
                }), 500
        else:
            # Evento no relevante, pero responder OK
            logger.info(f"ℹ️ Evento ignorado: {webhook_event}")
            return jsonify({
                'status': 'ignored',
                'message': f'Event {webhook_event} not processed'
            }), 200
            
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/test/send', methods=['POST'])
def test_send():
    """
    Endpoint de prueba para enviar mensajes manualmente
    Requiere: {"jid": "123456789@g.us", "message": "Texto del mensaje"}
    """
    try:
        data = request.json
        # Intentar obtener JID de: request > env > archivo
        jid = data.get('jid') or WHATSAPP_GROUP_JID
        
        if not jid:
             try:
                if os.path.exists("active_group.jid"):
                    with open("active_group.jid", "r") as f:
                        jid = f.read().strip()
             except:
                 pass
        
        message = data.get('message', '🧪 Mensaje de prueba')
        
        if not jid:
            return jsonify({'error': 'JID not provided and no active group found'}), 400
        
        success = whatsapp_bot.send_message(jid, message)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Test message sent'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send message'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    logger.info(f"🌐 Servidor webhook iniciando en puerto {PORT}...")
    logger.info(f"📱 WhatsApp Group JID: {WHATSAPP_GROUP_JID or 'NO CONFIGURADO'}")
    logger.info(f"🔐 Webhook Secret: {'Configurado' if WEBHOOK_SECRET else 'NO CONFIGURADO (no recomendado)'}")
    
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False
    )
