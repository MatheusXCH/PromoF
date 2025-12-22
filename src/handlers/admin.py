from sqlalchemy import func, desc
from models import Keyword, NegativeKeyword, MatchLog

async def handle_admin_commands(event, db):
    parts = event.raw_text.lower().split(maxsplit=1)
    cmd = parts[0]
    
    # .help
    if cmd == '.help':
        help_text = (
            "🤖 **PromoF Monitor - Central de Ajuda**\n\n"
            "**Comandos Administrativos:**\n"
            "• `.add <termo>`: Inicia monitoramento.\n"
            "• `.neg <termo>`: Adiciona exclusão.\n"
            "• `.list`: Lista filtros ativos.\n"
            "• `.remove <termo>`: Remove um filtro.\n"
            "• `.stats`: Exibe o relatório de matches e performance.\n"
            "• `.help`: Exibe esta mensagem."
        )
        await event.respond(help_text)
        return
    
    # .add
    if cmd == '.add' and len(parts) > 1:
        word = parts[1].strip()
        if not db.query(Keyword).filter_by(word=word).first():
            db.add(Keyword(word=word))
            db.commit()
            await event.respond(f"✅ Filtro **'{word}'** adicionado.")
            
    # .neg
    elif cmd == '.neg' and len(parts) > 1:
        word = parts[1].strip()
        if not db.query(NegativeKeyword).filter_by(word=word).first():
            db.add(NegativeKeyword(word=word))
            db.commit()
            await event.respond(f"🚫 Exclusão **'{word}'** adicionada.")
            
    # .remove
    elif (cmd == '.remove' or cmd == '.del') and len(parts) > 1:
        word = parts[1].strip()
        db.query(Keyword).filter_by(word=word).delete()
        db.commit()
        await event.respond(f"🗑️ Filtro **'{word}'** removido.")
        
    # .list
    elif cmd == '.list':
        kws = db.query(Keyword).all()
        negs = db.query(NegativeKeyword).all()
        msg = "🔍 **Filtros Ativos:**\n" + "\n".join(f"• {k.word}" for k in kws)
        msg += "\n\n🚫 **Exclusões:**\n" + "\n".join(f"• {n.word}" for n in negs)
        await event.respond(msg)
    
    # .stats
    if cmd == '.stats':
        # 1. Total de Matches
        total_matches = db.query(func.count(MatchLog.id)).scalar()
        
        # 2. Top 3 Keywords mais "pescadas" (Join entre MatchLog e Keyword)
        top_keywords = (
            db.query(Keyword.word, func.count(MatchLog.id).label('total'))
            .join(MatchLog, Keyword.id == MatchLog.keyword_id)
            .group_by(Keyword.word)
            .order_by(desc('total'))
            .limit(3).all()
        )
        
        # 3. Top 3 Canais de Origem
        top_channels = (
            db.query(MatchLog.channel_id, func.count(MatchLog.id).label('total'))
            .group_by(MatchLog.channel_id)
            .order_by(desc('total'))
            .limit(3).all()
        )

        # Montagem do Relatório
        report = [
            "📊 **Relatório de Performance - PromoF**",
            f"\n🔥 **Total de Matches:** {total_matches}",
            "\n🏆 **Top 3 Termos:**"
        ]
        
        for kw, count in top_keywords:
            report.append(f"• {kw}: {count}")
            
        report.append("\n📡 **Top 3 Canais Fontes:**")
        for ch, count in top_channels:
            report.append(f"• {ch}: {count}")
            
        report.append("\n_Dados extraídos em tempo real do PostgreSQL._")
        
        await event.respond("\n".join(report))
        return