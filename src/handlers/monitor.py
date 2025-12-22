import hashlib
from config import DESTINO
from models import Keyword, NegativeKeyword, MessageLog, MatchLog
from utils import extract_price, is_fuzzy_match

async def handle_promotion_filter(event, client, db):
    texto_lower = event.raw_text.lower()
    texto_words = texto_lower.split()

    # 1. Filtro de Negativas
    negativas = [n.word for n in db.query(NegativeKeyword).all()]
    if any(neg in texto_lower for neg in negativas):
        return

    # 2. Prevenção de Duplicatas
    msg_hash = hashlib.md5(texto_lower.encode('utf-8')).hexdigest()
    if db.query(MessageLog).filter_by(msg_hash=msg_hash).first():
        return

    # 3. Lógica de Match
    keywords = db.query(Keyword).all()
    for kw_obj in keywords:
        palavras_da_keyword = kw_obj.word.lower().split()
        match_confirmado = all(
            (p in texto_lower or is_fuzzy_match(p, texto_words)) 
            for p in palavras_da_keyword
        )

        if match_confirmado:
            usou_fuzzy = any(p not in texto_lower for p in palavras_da_keyword)
            preco = extract_price(event.raw_text)
            
            # Persistência de Auditoria
            db.add(MessageLog(msg_hash=msg_hash))
            try:
                chat = await event.get_chat()
                origem = getattr(chat, 'title', f"ID: {event.chat_id}")
            except: origem = "Origem Desconhecida"

            db.add(MatchLog(
                keyword_id=kw_obj.id, channel_id=origem,
                content_preview=texto_lower[:100], price_extracted=preco, is_fuzzy=usou_fuzzy
            ))
            db.commit()

            # Forwarding
            try:
                await client.forward_messages(DESTINO, event.message)
                print(f"🔥 Match: {kw_obj.word} | Preço: {preco}")
            except Exception as e:
                print(f"❌ Erro ao encaminhar: {e}")
            break