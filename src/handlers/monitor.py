import hashlib
from config import DESTINO
from models import Keyword, NegativeKeyword, MessageLog, MatchLog
from utils import extract_price, is_fuzzy_match, identify_store

async def handle_promotion_filter(event, client, db):
    texto_raw = event.raw_text
    texto_lower = texto_raw.lower()
    preco_atual = extract_price(texto_raw)
    loja_tag = identify_store(texto_raw)

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
    for kw in keywords:
        palavras_req = kw.word.split()
        match = all((p in texto_lower or is_fuzzy_match(p, texto_lower.split())) for p in palavras_req)

        if match:
            # FILTRO DE FAIXA DE PREÇO
            if kw.max_price and preco_atual:
                if preco_atual > kw.max_price:
                    print(f"⏩ Ignorado: {kw.word} (R$ {preco_atual} > R$ {kw.max_price})")
                    continue

            # SALVAR MATCH COM TAG DE LOJA
            db.add(MatchLog(
                keyword_id=kw.id,
                channel_id=f"{loja_tag} | {event.chat_id}",
                price_extracted=preco_atual,
                content_preview=texto_lower[:100]
            ))
            db.commit()

            await client.forward_messages(DESTINO, event.message)
            print(f"🔥 {loja_tag} | Match: {kw.word} | Preço: {preco_atual}")
            break