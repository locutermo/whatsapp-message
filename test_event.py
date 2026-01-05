from neonize.client import NewClient
from neonize.events import ConnectedEv, JoinedGroupEv
import logging

logging.basicConfig(level=logging.INFO)

def start_bot():
    client = NewClient("session.db")

    @client.event(ConnectedEv)
    def on_connected(client: NewClient, _):
        print("✅ ¡Bot conectado con éxito a WhatsApp!")

    @client.event(JoinedGroupEv)
    def on_group_join(client: NewClient, event: JoinedGroupEv):
        print("\n" + "="*50)
        print("🔍 DEBUGGING - Estructura del evento JoinedGroupEv:")
        print("="*50)
        
        # Imprimir todos los atributos del evento
        print("\n📋 Atributos disponibles:")
        for attr in dir(event):
            if not attr.startswith('_'):
                try:
                    value = getattr(event, attr)
                    if not callable(value):
                        print(f"  • {attr}: {value}")
                except Exception as e:
                    print(f"  • {attr}: Error al acceder - {e}")
        
        print("\n" + "="*50)
        
        # Intentar acceder a GroupInfo
        try:
            if hasattr(event, 'GroupInfo'):
                group_info = event.GroupInfo
                print("\n📦 GroupInfo encontrado:")
                print(f"  Tipo: {type(group_info)}")
                
                # Explorar GroupInfo
                for attr in dir(group_info):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(group_info, attr)
                            if not callable(value):
                                print(f"  • {attr}: {value}")
                        except:
                            pass
        except Exception as e:
            print(f"❌ Error al acceder a GroupInfo: {e}")
        
        print("="*50 + "\n")

    client.connect()

if __name__ == "__main__":
    start_bot()
