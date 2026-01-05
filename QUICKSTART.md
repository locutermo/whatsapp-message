# 🚀 Guía Rápida de Configuración

## Paso 1: Obtener el JID del Grupo de WhatsApp

Ya tienes una sesión activa, así que solo necesitas obtener el JID del grupo donde quieres recibir las notificaciones:

```bash
# El bot ya está conectado, solo añádelo a un grupo
# y verás el JID en la consola de los procesos que están corriendo
```

O ejecuta:
```bash
python3.10 get_group_jid.py
```

Copia el JID que aparece (formato: `123456789@g.us`)

## Paso 2: Configurar Variables de Entorno

Edita el archivo `.env` y completa:

```bash
# Pega el JID del grupo aquí
WHATSAPP_GROUP_JID=123456789@g.us

# Opcional: Credenciales de Jira (solo si necesitas consultar la API)
JIRA_EMAIL=tu-email@ejemplo.com
JIRA_API_TOKEN=tu-token-aqui
```

## Paso 3: Iniciar el Servidor Webhook

```bash
python3.10 webhook_server.py
```

El servidor estará disponible en `http://localhost:5000`

## Paso 4: Probar que Funciona

### Opción A: Test Local

```bash
curl -X POST http://localhost:5000/test/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "🧪 Prueba desde el servidor webhook"
  }'
```

Deberías recibir el mensaje en el grupo de WhatsApp.

### Opción B: Simular Webhook de Jira

```bash
curl -X POST http://localhost:5000/webhook/jira \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: mi-secreto-super-seguro-2026" \
  -d '{
    "webhookEvent": "jira:issue_created",
    "issue": {
      "key": "GHD-999",
      "fields": {
        "summary": "Ticket de prueba desde curl",
        "description": "Esta es una prueba de integración",
        "reporter": {"displayName": "Sistema de Pruebas"},
        "priority": {"name": "High"},
        "issuetype": {"name": "Incident"}
      }
    }
  }'
```

## Paso 5: Configurar Webhook en Jira

1. Ve a: https://integratelperu.atlassian.net/plugins/servlet/webhooks

2. Clic en **Create a Webhook**

3. Configura:
   - **Name**: WhatsApp Notifications
   - **Status**: ✅ Enabled
   - **URL**: `https://tu-servidor.com/webhook/jira` (o usa ngrok para pruebas locales)
   - **Events**: 
     - ✅ Issue → created
   - **JQL**: `project = GHD` (opcional, para filtrar solo ese proyecto)

4. En **Advanced** → **Headers**, añade:
   ```
   X-Webhook-Secret: mi-secreto-super-seguro-2026
   ```

## 🧪 Usar ngrok para Pruebas Locales

Si quieres probar sin desplegar a producción:

```bash
# Instalar ngrok (si no lo tienes)
brew install ngrok

# Exponer tu servidor local
ngrok http 5000
```

Copia la URL que te da ngrok (ej: `https://abc123.ngrok.io`) y úsala en la configuración del webhook de Jira:
```
https://abc123.ngrok.io/webhook/jira
```

## ✅ Verificar que Todo Funciona

1. **Health Check**:
   ```bash
   curl http://localhost:5000/health
   ```
   
   Deberías ver:
   ```json
   {
     "status": "ok",
     "bot_connected": true,
     "timestamp": "2026-01-05T01:30:00"
   }
   ```

2. **Crear un ticket de prueba en Jira** en el proyecto GHD

3. **Verificar que llegue el mensaje a WhatsApp** 🎉

## 🐛 Troubleshooting

### El bot no está conectado
```bash
# Verifica el estado
curl http://localhost:5000/health

# Si bot_connected es false, revisa los logs del servidor
```

### No llegan los mensajes
1. Verifica que `WHATSAPP_GROUP_JID` esté configurado correctamente
2. Verifica que el bot esté en el grupo
3. Revisa los logs del servidor

### Error en el webhook de Jira
1. Verifica que el `WEBHOOK_SECRET` coincida
2. Verifica que la URL sea accesible desde internet (usa ngrok para pruebas)
3. Revisa los logs en Jira: Settings → System → Webhooks → (tu webhook) → View details

## 📦 Desplegar a Producción (Square Cloud)

Una vez que todo funcione localmente:

1. Asegúrate de que `.env` tenga todas las variables configuradas
2. Sube el proyecto a Square Cloud
3. Configura las variables de entorno en Square Cloud
4. El servidor se iniciará automáticamente con `webhook_server.py`
