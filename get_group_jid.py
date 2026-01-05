#!/usr/bin/env python3.10
"""
Script de ayuda para obtener el JID de un grupo de WhatsApp
Ejecuta este script, escanea el QR y añade el bot a un grupo.
El JID se mostrará en la consola.
"""
from bot_whatsapp import WhatsAppBot

print("=" * 60)
print("🔍 OBTENER JID DE GRUPO DE WHATSAPP")
print("=" * 60)
print()
print("Instrucciones:")
print("1. Escanea el código QR que aparecerá")
print("2. Añade este número a un grupo de WhatsApp")
print("3. El JID del grupo se mostrará aquí")
print("4. Copia el JID y pégalo en el archivo .env")
print()
print("=" * 60)
print()

bot = WhatsAppBot()
bot.start()
bot.wait_forever()
