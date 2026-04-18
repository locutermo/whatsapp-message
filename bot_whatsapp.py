from neonize.client import NewClient
from neonize.events import ConnectedEv, JoinedGroupEv, MessageEv
from neonize.proto.Neonize_pb2 import JID
import logging
import threading
import os

logging.basicConfig(level=logging.INFO)

DATA_DIR = os.getenv("DATA_DIR", ".")
JID_FILE = os.path.join(DATA_DIR, "active_group.jid")

if DATA_DIR != "." and not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)


class WhatsAppBot:
    def __init__(self, session_file=None):
        self.client = None
        self.session_file = session_file or os.path.join(DATA_DIR, "session.db")
        self.is_connected = False
        self.connection_event = threading.Event()

    def setup_handlers(self):
        @self.client.event(ConnectedEv)
        def on_connected(client: NewClient, _):
            print("✅ ¡Bot conectado con éxito a WhatsApp!")
            self.is_connected = True
            self.connection_event.set()

        @self.client.event(MessageEv)
        def on_message(client: NewClient, event: MessageEv):
            # Ignorar mensajes propios
            if event.Info.MessageSource.IsFromMe:
                return

            # Extraer texto del mensaje
            msg_text = ""
            if event.Message.conversation:
                msg_text = event.Message.conversation
            elif event.Message.extendedTextMessage.text:
                msg_text = event.Message.extendedTextMessage.text

            # Verificar comando
            if msg_text.strip().lower() == "/group":
                chat_jid = event.Info.MessageSource.Chat

                # Construir string JID
                jid_str = f"{chat_jid.User}@{chat_jid.Server}"
                print(f"📝 Comando /group recibido desde: {jid_str}")

                try:
                    # Verificar si había un grupo anterior
                    old_jid = None
                    if os.path.exists(JID_FILE):
                        with open(JID_FILE, "r") as f:
                            old_jid = f.read().strip()

                    # Si había un grupo anterior y es diferente al actual, avisar
                    if old_jid and old_jid != jid_str:
                        print(f"🔄 Cambiando grupo de {old_jid} a {jid_str}")
                        self.send_message(
                            old_jid,
                            f"⚠️ **Notificaciones Desactivadas**\n\nLas notificaciones de Jira se han movido a otro chat por instrucción del usuario.",
                        )

                    # Guardar nuevo JID
                    with open(JID_FILE, "w") as f:
                        f.write(jid_str)
                    print(f"✅ JID actualizado a: {jid_str}")

                    self.send_message(
                        jid_str,
                        f"✅ **¡Configurado!**\n\nEste chat ({jid_str}) ha sido establecido como el destino para las notificaciones de Jira.",
                    )
                except Exception as e:
                    print(f"❌ Error al guardar JID: {e}")
                    self.send_message(
                        jid_str, f"❌ Error al guardar configuración: {e}"
                    )

        @self.client.event(JoinedGroupEv)
        def on_group_join(client: NewClient, event: JoinedGroupEv):
            group_jid = event.GroupInfo.JID

            jid_str = f"{group_jid.User}@{group_jid.Server}"
            print(f"📢 Fui añadido al grupo: {jid_str}")

            self.send_message(
                group_jid,
                f"👋 ¡Hola! Soy el bot de Jira.\n\nPara recibir notificaciones aquí, envía el comando: */group*\n\nDe lo contrario, seguiré usando la configuración por defecto.",
            )

    def start(self):
        """Inicia el cliente de WhatsApp"""
        logging.info(f"💾 Usando archivo de sesión: {self.session_file}")

        # Reset de sesión forzado o limpieza de archivo vacío
        should_reset = os.getenv("WHATSAPP_RESET_SESSION", "false").lower() == "true"

        if should_reset:
            logging.info(
                "🧹 Reset de sesión solicitado (WHATSAPP_RESET_SESSION=true), eliminando sesión..."
            )
            if os.path.exists(self.session_file):
                try:
                    os.remove(self.session_file)
                except Exception as e:
                    logging.error(f"❌ Error al intentar borrar la sesión: {e}")
        elif (
            os.path.exists(self.session_file)
            and os.path.getsize(self.session_file) == 0
        ):
            logging.info("🧹 Archivo de sesión vacío detectado, limpiando...")
            try:
                os.remove(self.session_file)
            except Exception as e:
                logging.error(f"❌ Error al intentar borrar la sesión vacía: {e}")

        self.client = NewClient(self.session_file)
        self.setup_handlers()

        phone_number = os.getenv("WHATSAPP_PHONE")

        def run_client():
            logging.info("⚡ Conectando cliente de WhatsApp en segundo plano...")
            try:
                def delayed_pair():
                    import time
                    # Esperar a que connect() establezca el socket interno (evita 'client is nil')
                    time.sleep(2)
                    if not self.client.is_logged_in and phone_number:
                        logging.info(
                            f"📲 Solicitando Pairing Code para el número: {phone_number}"
                        )
                        try:
                            self.client.PairPhone(phone_number, True)
                        except Exception as e:
                            logging.error(f"❌ Error al solicitar Pairing Code: {e}")

                threading.Thread(target=delayed_pair, daemon=True).start()

                # connect() es bloqueante, debe correr para que se inicie el socket
                self.client.connect()
            except Exception as e:
                logging.error(f"❌ Error crítico en la conexión de WhatsApp: {e}")

        self.client_thread = threading.Thread(target=run_client, daemon=True)
        self.client_thread.start()

        return self.client


    def send_message(self, jid, message: str):
        """
        Envía un mensaje a un JID específico

        Args:
            jid: JID del destinatario (puede ser str o objeto JID)
            message: Texto del mensaje a enviar
        """
        if not self.is_connected:
            print("❌ Error: El bot no está conectado")
            return False

        try:
            # Convertir string a objeto JID si es necesario
            jid_obj = jid
            if isinstance(jid, str):
                if "@" in jid:
                    user, server = jid.split("@")
                    # Construir JID manualmente para asegurar que todos los campos requeridos estén presentes
                    # build_jid de la librería a veces falla con grupos
                    jid_obj = JID(
                        User=user, Server=server, Device=0, RawAgent=0, Integrator=0
                    )
                else:
                    # Asumir usuario individual por defecto
                    jid_obj = JID(
                        User=jid,
                        Server="s.whatsapp.net",
                        Device=0,
                        RawAgent=0,
                        Integrator=0,
                    )

            self.client.send_message(jid_obj, message)
            print(f"✅ Mensaje enviado")
            return True
        except Exception as e:
            print(f"❌ Error al enviar mensaje: {e}")
            return False


# Instancia global del bot
bot_instance = None


def get_bot_instance():
    """Obtiene o crea la instancia global del bot"""
    global bot_instance
    if bot_instance is None:
        bot_instance = WhatsAppBot()
        bot_instance.start()
    return bot_instance
