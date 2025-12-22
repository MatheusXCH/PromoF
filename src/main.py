import logging
import asyncio
from telethon import TelegramClient, events
from config import API_ID, API_HASH, SESSION_PATH
from database import init_db, SessionLocal
from handlers.admin import handle_admin_commands
from handlers.monitor import handle_promotion_filter

# Logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

@client.on(events.NewMessage)
async def general_handler(event):
    if not event.raw_text:
        return

    db = SessionLocal()
    try:
        if event.is_private and event.raw_text.startswith('.'):
            await handle_admin_commands(event, db)
        else:
            await handle_promotion_filter(event, client, db)
    finally:
        db.close()

async def main():
    init_db()
    await client.start()
    print("🚀 Bot iniciado e modularizado!")
    await client.get_dialogs()
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass