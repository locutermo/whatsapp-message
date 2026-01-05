```mermaid
graph TB
    subgraph "Jira Service Desk"
        A[Usuario crea ticket en GHD]
        B[Jira Webhook]
    end
    
    subgraph "Tu Servidor"
        C[webhook_server.py<br/>Flask Server]
        D[bot_whatsapp.py<br/>WhatsApp Client]
    end
    
    subgraph "WhatsApp"
        E[Grupo de WhatsApp]
        F[Equipo de Soporte]
    end
    
    A -->|Trigger| B
    B -->|POST /webhook/jira| C
    C -->|Formatea mensaje| C
    C -->|send_message| D
    D -->|Envía notificación| E
    E -->|Notifica| F
    
    style A fill:#0052CC
    style B fill:#0052CC
    style C fill:#25D366
    style D fill:#25D366
    style E fill:#128C7E
    style F fill:#075E54
```

## Flujo de Datos

1. **Usuario crea ticket** en Jira Service Desk (proyecto GHD)
2. **Jira dispara webhook** con los datos del ticket
3. **Servidor Flask recibe** el webhook en `/webhook/jira`
4. **Servidor formatea** la información del ticket en un mensaje bonito
5. **Bot de WhatsApp envía** el mensaje al grupo configurado
6. **Equipo de soporte** recibe la notificación instantánea

## Formato del Mensaje

```
🎫 *Nuevo Ticket en Jira*

📋 *Incident:* GHD-123
📝 *Título:* Sistema no responde
👤 *Reportado por:* Juan Pérez
⚡ *Prioridad:* High

📄 *Descripción:*
El sistema presenta errores al intentar...

🔗 *Ver ticket:* https://integratelperu.atlassian.net/browse/GHD-123

⏰ *Creado:* 2026-01-05 01:30:00
```
