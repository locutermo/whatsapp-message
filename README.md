# 🤖 Bot de WhatsApp + Integración con Jira

Bot automatizado de WhatsApp que recibe notificaciones de Jira Service Desk y las envía a grupos de WhatsApp. Optimizada para despliegue en la nube (Zeabur/Docker).

## 📋 Características

- ✅ **Pairing Code**: Vinculación sin necesidad de escanear QR (ideal para servidores remotos).
- ✅ **Dynamic Grouping**: Configuración de grupo de destino mediante el comando `/group`.
- ✅ **Session Management**: Mecanismo de reset forzado para solucionar bloqueos de inicio de sesión.
- ✅ **Dockerized**: Listo para desplegar en cualquier plataforma con soporte Docker.
- ✅ **Formato profesional**: Mensajes claros con información relevante del ticket de Jira.

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia el archivo `.env.example` a `.env` y configura tus credenciales:

```bash
cp .env.example .env
```

Variables principales:
- `WHATSAPP_PHONE`: Tu número de teléfono (con código de país, ej: `519XXXXXXXX`).
- `WHATSAPP_GROUP_JID`: (Opcional) JID inicial del grupo.
- `WEBHOOK_SECRET`: Secreto para validar peticiones de Jira.
- `WHATSAPP_RESET_SESSION`: Establecer a `true` si el login se queda pegado.

## 🎯 Configuración de WhatsApp (Pairing Code)

En lugar de QR, este bot usa un **Código de Emparejamiento** de 8 dígitos:

1. Inicia el bot (`python main.py`).
2. En los logs/consola verás un mensaje: `📲 Solicitando Pairing Code para el número: ...`.
3. Un código de 8 caracteres aparecerá (ej: `ABC1-DEF2`).
4. En tu celular (WhatsApp → Dispositivos vinculados → Vincular dispositivo → **Vincular con el número de teléfono**), ingresa el código.

## 🔧 Uso y Comandos

### Punto de entrada (Producción)
```bash
python main.py
```

### Configurar el grupo de destino
Una vez que el bot esté conectado:
1. Añade el bot a un grupo de WhatsApp.
2. Dentro del grupo, escribe el comando: **/group**.
3. El bot confirmará que ese chat recibirá las notificaciones de Jira.

## 📦 Despliegue en Zeabur

Este proyecto está optimizado para Zeabur:
1. El `Dockerfile` expone el puerto `5000`.
2. Se usa `main.py` para manejar dinámicamente el puerto asignado por la plataforma.
3. Asegúrate de configurar las variables de entorno en el panel de Zeabur.
4. Usa los **Runtime Logs** para obtener el Pairing Code en el primer inicio.

## 📁 Estructura del Proyecto

```
whatsapp-message/
├── main.py              # Punto de entrada principal (Bootstrap)
├── bot_whatsapp.py      # Lógica del cliente WhatsApp (Neonize)
├── webhook_server.py    # Servidor Flask para Webhooks de Jira
├── Dockerfile           # Configuración para despliegue en contenedores
├── Procfile             # Configuración para despliegue en PaaS
├── requirements.txt     # Dependencias del proyecto
└── active_group.jid     # Archivo persistente con el ID del grupo actual
```

## 🐛 Troubleshooting

### El bot se queda en "Iniciando sesión..." infinitamente
Esto ocurre por un archivo de sesión corrupto ("Zombie file").
1. Establece `WHATSAPP_RESET_SESSION=true` en tus variables de entorno.
2. Reinicia el servicio. El archivo de sesión se borrará automáticamente.
3. Vincula de nuevo con el nuevo código generado.
4. Cambia `WHATSAPP_RESET_SESSION` a `false`.

### Error "no sender key for..."
Es normal al inicio de una sesión o al entrar a un grupo nuevo. **Envía un mensaje nuevo al grupo desde otro teléfono** para forzar el intercambio de llaves.

---
Basado en la librería [neonize](https://github.com/krypton-byte/neonize).
