import logging
import asyncio
from telethon import TelegramClient, events
from config import API_ID, API_HASH, SESSION_PATH, BOT_TOKEN, DESTINO
from database import init_db, SessionLocal
from handlers.admin import handle_admin_commands
from handlers.monitor import handle_promotion_filter

# Logging configurado para o ambiente Docker no Proxmox
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO)

# ━━━ CLIENTES HÍBRIDOS ━━━
# Cliente 1: Sua conta (UserBot) - Atua como "Ouvinte"
user_client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# Cliente 2: Bot Oficial (Bot API) - Atua como "Notificador"
# O arquivo 'bot_session' será gerado automaticamente no volume de dados
bot_client = TelegramClient('/app/data/bot_session', API_ID, API_HASH)

@user_client.on(events.NewMessage(blacklist_chats=[DESTINO]))
async def general_handler(event):
    if event.chat_id == DESTINO:
        return
    
    if not event.raw_text:
        return

    db = SessionLocal()
    try:
        # 1. ISOLAMENTO DE PRIVADOS (Mensagens Salvas e Comandos)
        if event.is_private:
            # Só processa se for um comando administrativo
            if event.raw_text.startswith('.'):
                await handle_admin_commands(event, db)
            # Ignora qualquer outra mensagem privada (evita capturar "Mensagens Salvas")
            return 
        
        # 2. MONITORAMENTO DE CANAIS E GRUPOS
        # Como o DESTINO está na blacklist, este bloco nunca processará o próprio canal PromoF
        else:
            await handle_promotion_filter(event, bot_client, db)
            
    finally:
        db.close()

async def main():
    init_db()
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    
    welcome_msg = (
        "🚀 **SISTEMA PROMOF INICIADO**\n"
        "─── ⋆ ───\n"
        "🤖 **Status:** `Online & Monitorando`\n"
        "🏗️ **Modo:** `Híbrido (User Bot + Bot API)`\n"
        "🏠 **Ambiente:** `Docker Container`\n\n"
        "🔔 *Notificações Push habilitadas via Bot API.*"
    )
    
    try:
        await bot_client.send_message(DESTINO, welcome_msg, parse_mode='markdown')
        print("✅ Mensagem de boas-vindas enviada com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro ao enviar boas-vindas: {e}")
    
    print("🚀 PromoF Bot Inicializado!")
    
    await user_client.get_dialogs()
    # Mantém o loop ativo para o cliente ouvinte
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass