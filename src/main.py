import logging
import asyncio
from telethon import TelegramClient, events
from config import API_ID, API_HASH, MONITOR_SESSION_PATH, NOTIFIER_SESSION_PATH, BOT_TOKEN, DESTINO
from database import init_db, SessionLocal
from handlers.admin import handle_admin_commands
from handlers.monitor import handle_promotion_filter
from utils import setup_logging

setup_logging()
logger = logging.getLogger("MAIN")

user_client = TelegramClient(MONITOR_SESSION_PATH, API_ID, API_HASH)
bot_client = TelegramClient(NOTIFIER_SESSION_PATH, API_ID, API_HASH)

@user_client.on(events.NewMessage(blacklist_chats=[DESTINO]))
async def general_handler(event):
    """
    Orquestra a triagem inicial de todas as mensagens recebidas pelo UserBot.

    Aplica filtros de segurança anti-loop, separa comandos administrativos de 
    processamento de monitoramento e gerencia o ciclo de vida da conexão com o banco.

    Args:
        event (NewMessage.Event): O evento bruto capturado pelo Telegram.
    """
    
    if event.chat_id == DESTINO:
        return
    
    if not event.raw_text:
        return

    db = SessionLocal()
    try:
        if event.is_private:
            if event.raw_text.startswith('.'):
                await handle_admin_commands(event, db)
            return 
        
        else:
            await handle_promotion_filter(event, bot_client, db)
            
    finally:
        db.close()

async def main():
    """
    Ponto de entrada assíncrono para inicialização de todos os serviços.

    Carrega variáveis de ambiente, inicializa o banco de dados e estabelece a 
    conexão persistente de ambos os clientes (UserBot e Bot API).
    """
    
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
        logger.info("✅ Mensagem de boas-vindas enviada com sucesso!")
    except Exception as e:
        logger.info(f"⚠️ Erro ao enviar boas-vindas: {e}")
    
    logger.info("🚀 PromoF Bot Inicializado!")
    
    await user_client.get_dialogs()
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass