import re
from sqlalchemy import func, desc
from models import Keyword, NegativeKeyword, MatchLog

async def handle_admin_commands(event, db):
    raw_text = event.raw_text
    parts = raw_text.split()
    if not parts: return
    
    cmd = parts[0].lower()
    
    # .help
    if cmd == '.help':
        help_text = (
            "🤖 **Guia de Comandos PromoF**\n\n"
            "**Adicionar Filtros:**\n"
            "• `.add rtx 4060` -> Monitora o termo completo, ignorando filtros de preço.\n"
            "• `.add rtx 4060 -p 2000` -> Monitora 'rtx 4060' apenas se for **R$ 2000 ou menos**.\n\n"
            "**Outros Comandos:**\n"
            "• `.list`: Mostra seus termos e limites atuais.\n"
            "• `.stats`: Resumo de captura e performance.\n"
            "• `.history <termo>`: Últimos matches da keyword.\n"
            "• `.neg <termo>`: Bloqueia mensagens com esta palavra."
        )
        await event.respond(help_text)
    
    # .add
    elif cmd == '.add' and len(parts) > 1:
        # Pega tudo que vem depois do ".add"
        full_content = raw_text[len(cmd):].strip()
        
        max_price = None
        word = full_content

        # Verifica se a flag -p (case insensitive) existe no comando
        if " -p " in full_content.lower():
            # Divide a string na primeira ocorrência de -p
            # Usamos regex para garantir que pegamos o "-p" isolado
            split_parts = re.split(r' -p ', full_content, flags=re.IGNORECASE, maxsplit=1)
            
            word = split_parts[0].strip().lower()
            price_str = split_parts[1].strip().replace(',', '.')
            
            try:
                max_price = float(price_str)
            except ValueError:
                await event.respond("❌ **Erro:** O valor após `-p` deve ser um número válido.")
                return
        else:
            # Sem a flag, monitoramos o termo completo (ex: "rtx 4060")
            word = full_content.lower()

        # Persistência no banco
        if not db.query(Keyword).filter_by(word=word).first():
            db.add(Keyword(word=word, max_price=max_price))
            db.commit()
            
            status = f"💰 com preço até **R$ {max_price:.2f}**" if max_price else "🔓 sem limite de preço"
            await event.respond(f"✅ **Monitorando:** `{word}`\n⚖️ **Regra:** {status}")
        else:
            await event.respond(f"⚠️ O termo `{word}` já está na sua lista.")
        return
            
    # .neg
    elif cmd == '.neg' and len(parts) > 1:
        word = parts[1].strip()
        if not db.query(NegativeKeyword).filter_by(word=word).first():
            db.add(NegativeKeyword(word=word))
            db.commit()
            await event.respond(f"🚫 Exclusão **'{word}'** adicionada.")
            
    # .remove
    elif (cmd == '.remove' or cmd == '.del') and len(parts) > 1:
        # Captura todo o texto após o comando para suportar termos compostos
        word = raw_text[len(cmd):].strip().lower()
        
        # Busca a keyword exata no banco
        keyword_entry = db.query(Keyword).filter_by(word=word).first()
        
        if keyword_entry:
            db.delete(keyword_entry)
            db.commit()
            await event.respond(f"🗑️ Filtro **'{word}'** removido com sucesso.")
        else:
            await event.respond(f"⚠️ O termo **'{word}'** não foi encontrado na lista ativa.")
        
    # .list
    elif cmd == '.list':
        kws = db.query(Keyword).all()
        negs = db.query(NegativeKeyword).all()
        
        kw_lines = []
        for k in kws:
            # Monta a linha com o preço se ele existir no banco
            line = f"• {k.word}"
            if k.max_price:
                line += f" (até R$ {k.max_price:.2f})"
            kw_lines.append(line)
            
        msg = "🔍 **Filtros Ativos:**\n" + ("\n".join(kw_lines) if kw_lines else "⚠️ Nenhum filtro ativo.")
        
        if negs:
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
    
    # .history <termo>
    elif cmd == '.history' and len(parts) > 1:
        search_word = " ".join(parts[1:]).lower()
        kw = db.query(Keyword).filter_by(word=search_word).first()
        
        if not kw:
            await event.respond("❌ Keyword não encontrada.")
            return

        matches = (
            db.query(MatchLog)
            .filter(MatchLog.keyword_id == kw.id)
            .order_by(desc(MatchLog.created_at))
            .limit(5).all()
        )

        if not matches:
            await event.respond(f"📭 Sem histórico recente para '{search_word}'.")
            return

        res = [f"📚 **Histórico Recente: {search_word}**"]
        for m in matches:
            date = m.created_at.strftime("%d/%m %H:%M")
            price = f"R$ {m.price_extracted:.2f}" if m.price_extracted else "N/A"
            res.append(f"🕒 {date} | 💰 {price} | 📡 {m.channel_id}")
        
        await event.respond("\n".join(res))
        return