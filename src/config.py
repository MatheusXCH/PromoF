import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN') 
DESTINO_RAW = os.getenv('DESTINO')
MONITOR_SESSION_PATH = '/app/data/monitor_session'
NOTIFIER_SESSION_PATH = '/app/data/bot_session'

try:
    if DESTINO_RAW.startswith('-') or DESTINO_RAW.isdigit():
        DESTINO = int(DESTINO_RAW)
    else:
        DESTINO = DESTINO_RAW
except (ValueError, TypeError):
    DESTINO = DESTINO_RAW