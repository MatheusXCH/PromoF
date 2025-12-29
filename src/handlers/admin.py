import re
from sqlalchemy import func, desc
from models import Keyword, NegativeKeyword, MatchLog

def get_header(title, emoji):
    return f"{emoji} ━━━ **{title.upper()}** ━━━\n"

async def handle_admin_commands(event, db):
    raw_text = event.raw_text
    parts = raw_text.split()
    if not parts: return
    
    cmd = parts[0].lower()
    
    if cmd == '.help':
        help_text = (
            f"{get_header('Central de Ajuda', '🤖')}\n"
            "🔵 **GESTÃO DE FILTROS**\n"
            "• `.add <termo>`: Monitora sem limite.\n"
            "• `.add <termo> -p <valor>`: Monitora com teto.\n"
            "• `.remove <termo>`: Remove filtro existente.\n\n"
            "🔴 **EXCLUSÕES (BLACKLIST)**\n"
            "• `.neg <termo>`: Ignora mensagens com a palavra.\n\n"
            "📊 **ANÁLISE E STATUS**\n"
            "• `.list`: Lista filtros e preços atuais.\n"
            "• `.stats`: Dashboard de performance.\n"
            "• `.history <termo>`: Últimos 5 matches do termo.\n\n"
            "💡 _Toque em um comando para copiar._"
        )
        await event.respond(help_text)

    elif cmd == '.add' and len(parts) > 1:
        full_content = raw_text[len(cmd):].strip()
        max_price = None
        word = full_content

        if " -p " in full_content.lower():
            split_parts = re.split(r' -p ', full_content, flags=re.IGNORECASE, maxsplit=1)
            word = split_parts[0].strip().lower()
            try:
                max_price = float(split_parts[1].strip().replace(',', '.'))
            except ValueError:
                await event.respond("❌ **Erro:** O valor após `-p` deve ser numérico.")
                return
        else:
            word = full_content.lower()

        if not db.query(Keyword).filter_by(word=word).first():
            db.add(Keyword(word=word, max_price=max_price))
            db.commit()
            status = f"💰 até **R$ {max_price:.2f}**" if max_price else "🔓 sem limite"
            await event.respond(f"✅ **Monitorando:** `{word}`\n⚖️ **Regra:** {status}")
        else:
            await event.respond(f"⚠️ O termo `{word}` já está na lista.")

    elif cmd == '.list':
        kws = db.query(Keyword).all()
        negs = db.query(NegativeKeyword).all()
        
        msg = get_header("Filtros Ativos", "🔍")
        if not kws:
            msg += "_Nenhum filtro configurado._\n"
        else:
            for k in kws:
                price_tag = f" ➔ `R$ {k.max_price:.2f}`" if k.max_price else " ➔ `Livre`"
                msg += f"🟢 `{k.word.ljust(15)}` {price_tag}\n"
            
        if negs:
            msg += f"\n{get_header('Exclusões', '🚫')}"
            msg += ", ".join([f"`{n.word}`" for n in negs])
            
        await event.respond(msg)

    elif (cmd == '.remove' or cmd == '.del') and len(parts) > 1:
        word = raw_text[len(cmd):].strip().lower()
        keyword_entry = db.query(Keyword).filter_by(word=word).first()
        
        if keyword_entry:
            db.delete(keyword_entry)
            db.commit()
            await event.respond(f"🗑️ Filtro **'{word}'** removido com sucesso.")
        else:
            await event.respond(f"⚠️ Termo **'{word}'** não encontrado.")

    elif cmd == '.stats':
        total = db.query(func.count(MatchLog.id)).scalar()
        
        top_kw = db.query(Keyword.word, func.count(MatchLog.id).label('cnt'))\
                   .join(MatchLog).group_by(Keyword.word).order_by(desc('cnt')).first()

        top_ch = db.query(MatchLog.channel_id, func.count(MatchLog.id).label('cnt'))\
                   .group_by(MatchLog.channel_id).order_by(desc('cnt')).first()

        stats_msg = (
            f"{get_header('Performance', '📊')}\n"
            f"📈 **Total Capturado:** `{total}`\n"
            f"🏆 **Top Termo:** `{top_kw.word if top_kw else 'N/A'}`\n"
            f"📡 **Principal Fonte:** `{top_ch.channel_id if top_ch else 'N/A'}`\n"
            f"🛠️ **Ambiente:** `Proxmox/Docker`"
        )
        await event.respond(stats_msg)

    elif cmd == '.history' and len(parts) > 1:
        search_word = raw_text[len(cmd):].strip().lower()
        kw = db.query(Keyword).filter_by(word=search_word).first()
        
        if not kw:
            await event.respond("❌ Keyword não encontrada.")
            return

        matches = db.query(MatchLog).filter(MatchLog.keyword_id == kw.id)\
                    .order_by(desc(MatchLog.created_at)).limit(5).all()

        if not matches:
            await event.respond(f"📭 Sem histórico para `{search_word}`.")
            return

        res = [get_header(f"Histórico: {search_word}", "📚")]
        for m in matches:
            date = m.created_at.strftime("%d/%m %H:%M")
            price = f"R$ {m.price_extracted:.2f}" if m.price_extracted else "N/A"
            res.append(f"🕒 {date} | 💰 {price} | 📡 {m.channel_id[:15]}")
        
        await event.respond("\n".join(res))

    elif cmd == '.neg' and len(parts) > 1:
        word = parts[1].strip().lower()
        if not db.query(NegativeKeyword).filter_by(word=word).first():
            db.add(NegativeKeyword(word=word))
            db.commit()
            await event.respond(f"🚫 Palavra **'{word}'** adicionada às exclusões.")