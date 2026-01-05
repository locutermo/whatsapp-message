from neonize.client import NewClient
from neonize.events import ConnectedEv, JoinedGroupEv, MessageEv
from neonize.proto.Neonize_pb2 import JID
from neonize.utils import build_jid
import logging
import threading
import time
import os

logging.basicConfig(level=logging.INFO)

# Configuración de rutas
DATA_DIR = os.getenv('DATA_DIR', '.')
JID_FILE = os.path.join(DATA_DIR, "active_group.jid")

# Asegurar que el directorio de datos existe
if DATA_DIR != '.' and not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

class WhatsAppBot:
    def __init__(self, session_file=None):
        self.client = None
        # Si no se especifica, usar ruta en DATA_DIR
        self.session_file = session_file or os.path.join(DATA_DIR, "session.db")
        self.is_connected = False
        self.connection_event = threading.Event()
        
    def setup_handlers(self):
        """Configura los manejadores de eventos"""
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
                            f"⚠️ **Notificaciones Desactivadas**\n\nLas notificaciones de Jira se han movido a otro chat por instrucción del usuario."
                        )

                    # Guardar nuevo JID
                    with open(JID_FILE, "w") as f:
                        f.write(jid_str)
                    print(f"✅ JID actualizado a: {jid_str}")
                    
                    self.send_message(
                        jid_str,
                        f"✅ **¡Configurado!**\n\nEste chat ({jid_str}) ha sido establecido como el destino para las notificaciones de Jira."
                    )
                except Exception as e:
                    print(f"❌ Error al guardar JID: {e}")
                    self.send_message(
                        jid_str,
                        f"❌ Error al guardar configuración: {e}"
                    )

        @self.client.event(JoinedGroupEv)
        def on_group_join(client: NewClient, event: JoinedGroupEv):
            group_jid = event.GroupInfo.JID
            
            # Formatear JID como string
            jid_str = f"{group_jid.User}@{group_jid.Server}"
            print(f"📢 Fui añadido al grupo: {jid_str}")
            
            # Mensaje de bienvenida (sin autoguardado)
            self.send_message(
                group_jid, 
                f"👋 ¡Hola! Soy el bot de Jira.\n\nPara recibir notificaciones aquí, envía el comando: */group*\n\nDe lo contrario, seguiré usando la configuración por defecto."
            )
    
    def start(self):
        """Inicia el cliente de WhatsApp"""
        self.client = NewClient(self.session_file)
        self.setup_handlers()
        
        # Iniciar en un thread separado para no bloquear
        def run_client():
            self.client.connect()
        
        client_thread = threading.Thread(target=run_client, daemon=True)
        client_thread.start()
        
        # Esperar a que se conecte (máximo 30 segundos)
        if not self.connection_event.wait(timeout=30):
            print("⚠️ Advertencia: El bot no se conectó en 30 segundos")
        
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
                if '@' in jid:
                    user, server = jid.split('@')
                    # Construir JID manualmente para asegurar que todos los campos requeridos estén presentes
                    # build_jid de la librería a veces falla con grupos
                    jid_obj = JID(
                        User=user, 
                        Server=server,
                        Device=0,
                        RawAgent=0,
                        Integrator=0
                    )
                else:
                    # Asumir usuario individual por defecto
                    jid_obj = JID(
                        User=jid, 
                        Server="s.whatsapp.net",
                        Device=0,
                        RawAgent=0,
                        Integrator=0
                    )

            self.client.send_message(jid_obj, message)
            print(f"✅ Mensaje enviado")
            return True
        except Exception as e:
            print(f"❌ Error al enviar mensaje: {e}")
            return False
    
    def wait_forever(self):
        """Mantiene el bot ejecutándose indefinidamente"""
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Bot detenido por el usuario")

# Instancia global del bot
bot_instance = None

def get_bot_instance():
    """Obtiene o crea la instancia global del bot"""
    global bot_instance
    if bot_instance is None:
        bot_instance = WhatsAppBot()
        bot_instance.start()
    return bot_instance

if __name__ == "__main__":
    # Modo standalone: solo ejecuta el bot
    bot = WhatsAppBot()
    bot.start()
    bot.wait_forever()