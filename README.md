# 🤖 Bot de WhatsApp + Integración con Jira

Bot automatizado de WhatsApp que recibe notificaciones de Jira Service Desk y las envía a grupos de WhatsApp.

## 📋 Características

- ✅ Conexión automática a WhatsApp mediante QR
- ✅ Detección de cuando es añadido a grupos
- ✅ Servidor webhook para recibir notificaciones de Jira
- ✅ Envío automático de mensajes cuando se crean tickets
- ✅ Formato profesional de mensajes con información del ticket

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip3.10 install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia el archivo `.env.example` a `.env` y configura tus credenciales:

```bash
cp .env.example .env
```

Edita el archivo `.env`:

```env
# Configuración de Jira
JIRA_URL=https://integratelperu.atlassian.net
JIRA_EMAIL=tu-email@ejemplo.com
JIRA_API_TOKEN=tu-api-token-aqui

# Configuración de WhatsApp
WHATSAPP_GROUP_JID=123456789@g.us

# Configuración del servidor webhook
WEBHOOK_SECRET=tu-secreto-seguro-aqui
PORT=5000
```

### 3. Obtener el JID del grupo de WhatsApp

Primero, ejecuta el bot en modo standalone para obtener el JID del grupo:

```bash
python3.10 bot_whatsapp.py
```

1. Escanea el código QR con tu WhatsApp
2. Añade el bot a un grupo
3. El bot te mostrará el JID del grupo en la consola
4. Copia ese JID y pégalo en `.env` como `WHATSAPP_GROUP_JID`

### 4. Crear API Token de Jira

1. Ve a: https://id.atlassian.com/manage-profile/security/api-tokens
2. Clic en "Create API token"
3. Dale un nombre descriptivo (ej: "WhatsApp Bot")
4. Copia el token y pégalo en `.env` como `JIRA_API_TOKEN`

## 🎯 Uso

### Modo 1: Solo Bot de WhatsApp

```bash
python3.10 bot_whatsapp.py
```

### Modo 2: Servidor Webhook + Bot (Recomendado)

```bash
python3.10 webhook_server.py
```

El servidor estará disponible en `http://localhost:5000`

### Endpoints disponibles:

- **GET** `/health` - Verificar estado del servidor y bot
- **POST** `/webhook/jira` - Recibir webhooks de Jira
- **POST** `/test/send` - Enviar mensaje de prueba

## 🔧 Configurar Webhook en Jira

1. Ve a **Jira Settings** → **System** → **Webhooks**
2. Clic en **Create a Webhook**
3. Configura:
   - **Name**: WhatsApp Notifications
   - **Status**: Enabled
   - **URL**: `https://tu-servidor.com/webhook/jira`
   - **Events**: Issue → created
   - **JQL**: `project = GHD` (para filtrar solo el proyecto GHD)

4. En los headers, añade (opcional pero recomendado):
   ```
   X-Webhook-Secret: tu-secreto-seguro-aqui
   ```

## 🧪 Probar la integración

### 1. Verificar que el servidor está corriendo:

```bash
curl http://localhost:5000/health
```

### 2. Enviar mensaje de prueba:

```bash
curl -X POST http://localhost:5000/test/send \
  -H "Content-Type: application/json" \
  -d '{
    "jid": "123456789@g.us",
    "message": "🧪 Prueba de integración Jira-WhatsApp"
  }'
```

### 3. Simular webhook de Jira:

```bash
curl -X POST http://localhost:5000/webhook/jira \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: tu-secreto-seguro-aqui" \
  -d '{
    "webhookEvent": "jira:issue_created",
    "issue": {
      "key": "GHD-123",
      "fields": {
        "summary": "Ticket de prueba",
        "description": "Esta es una descripción de prueba",
        "reporter": {"displayName": "Juan Pérez"},
        "priority": {"name": "High"},
        "issuetype": {"name": "Incident"}
      }
    }
  }'
```

## 📦 Despliegue en Square Cloud

El archivo `square.cloud` ya está configurado. Solo necesitas:

1. Asegurarte de que el archivo `.env` esté configurado
2. Cambiar `MAIN=bot_whatsapp.py` a `MAIN=webhook_server.py` en `square.cloud`
3. Subir el proyecto a Square Cloud

## 🔒 Seguridad

- ⚠️ **Nunca** compartas tu archivo `.env`
- ⚠️ **Nunca** subas `session.db` a repositorios públicos
- ✅ Usa siempre `WEBHOOK_SECRET` en producción
- ✅ Usa HTTPS en producción (no HTTP)

## 📁 Estructura del Proyecto

```
whatsapp-message/
├── bot_whatsapp.py      # Cliente de WhatsApp (clase reutilizable)
├── webhook_server.py    # Servidor Flask para webhooks
├── requirements.txt     # Dependencias Python
├── .env.example        # Plantilla de variables de entorno
├── .env                # Variables de entorno (NO SUBIR A GIT)
├── session.db          # Sesión de WhatsApp (NO SUBIR A GIT)
├── square.cloud        # Configuración para Square Cloud
└── README.md           # Este archivo
```

## 🐛 Troubleshooting

### El bot no se conecta a WhatsApp
- Verifica que `session.db` tenga permisos de lectura/escritura
- Intenta eliminar `session.db` y volver a escanear el QR

### No llegan las notificaciones de Jira
- Verifica que el webhook esté configurado correctamente en Jira
- Revisa los logs del servidor con `tail -f logs.txt`
- Verifica que `WHATSAPP_GROUP_JID` esté correctamente configurado

### Error "libmagic not found"
```bash
brew install libmagic
```

## 📞 Soporte

Para más información sobre la librería neonize:
- GitHub: https://github.com/krypton-byte/neonize
- PyPI: https://pypi.org/project/neonize/
