import hashlib
import logging
from config import DESTINO
from models import Keyword, NegativeKeyword, MessageLog, MatchLog
from utils import extract_price, is_fuzzy_match, identify_store

async def handle_promotion_filter(event, bot_client, db):
    """
    Pipeline de Ingestão: Captura mensagens via UserBot e notifica via Bot API.
    Filtra ruídos de comentários/threads e duplicatas.
    """
    # ━━━ SOLUÇÃO 1: FILTRAR RESPOSTAS (THREADS/COMENTÁRIOS) ━━━
    # Se a mensagem for uma resposta a outra, ignoramos para capturar apenas posts originais
    if event.is_reply:
        return

    texto_raw = event.raw_text
    texto_lower = texto_raw.lower()
    
    # 1. Extração de Metadados e Linhagem
    preco_atual = extract_price(texto_raw)
    loja_tag = identify_store(texto_raw)
    
    try:
        # Recupera o nome amigável do canal/grupo
        chat = await event.get_chat()
        origem_nome = getattr(chat, 'title', getattr(chat, 'first_name', f"ID: {event.chat_id}"))
        
        # Gera link profundo para você poder abrir a postagem direto no celular
        if getattr(chat, 'username', None):
            link_origem = f"https://t.me/{chat.username}/{event.id}"
        else:
            link_origem = "🔒 Grupo Privado"
    except Exception:
        origem_nome = "Origem Desconhecida"
        link_origem = "Link indisponível"

    # 2. Filtro de Negativas
    negativas = [n.word for n in db.query(NegativeKeyword).all()]
    if any(neg in texto_lower for neg in negativas):
        return

    # 3. Deduplicação (MD5)
    msg_hash = hashlib.md5(texto_lower.encode('utf-8')).hexdigest()
    if db.query(MessageLog).filter_by(msg_hash=msg_hash).first():
        return

    # 4. Engine de Match
    keywords = db.query(Keyword).all()
    for kw in keywords:
        palavras_req = kw.word.split()
        match = all(
            (p in texto_lower or is_fuzzy_match(p, texto_lower.split())) 
            for p in palavras_req
        )

        if match:
            # Filtro de Teto de Preço
            if kw.max_price and preco_atual:
                if preco_atual > kw.max_price:
                    continue

            # ━━━ SOLUÇÃO 2: NOTIFICAÇÃO VIA BOT API ━━━
            # Montagem da mensagem formatada para garantir o som e banner no celular
            msg_formatada = (
                f"🔥 **{kw.word.upper()} ENCONTRADO!**\n"
                f"─── ⋆ ───\n"
                f"💰 **Preço:** `R$ {preco_atual if preco_atual else 'N/A'}`\n"
                f"{loja_tag} | 📡 **Fonte:** `{origem_nome}`\n\n"
                f"📝 **Resumo:**\n_{texto_raw[:300]}..._\n\n"
                f"🔗 [ABRIR OFERTA ORIGINAL]({link_origem})"
            )

            try:
                # O bot_client é quem realiza o envio no canal DESTINO
                await bot_client.send_message(
                    DESTINO, 
                    msg_formatada, 
                    link_preview=False,
                    parse_mode='markdown'
                )
                
                # Persistência no PostgreSQL
                db.add(MessageLog(msg_hash=msg_hash))
                db.add(MatchLog(
                    keyword_id=kw.id,
                    channel_id=origem_nome,
                    content_preview=texto_lower[:100],
                    price_extracted=preco_atual
                ))
                db.commit()
                print(f"✅ Notificado: {kw.word} ({origem_nome})")
            except Exception as e:
                print(f"❌ Erro na notificação: {e}")
            
            break 

    db.close()