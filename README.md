# PromoF - Monitor de Ofertas Híbrido 🚀

O **PromoF** é um ecossistema de monitoramento de ofertas em tempo real para o Telegram, projetado para rodar de forma eficiente em ambientes de **Home Lab** (Proxmox/Docker). O projeto utiliza uma **Arquitetura Híbrida** para maximizar a performance e a qualidade das notificações.

## 📋 Sumário
1. [Visão Geral](#visão-geral)
2. [Passo a Passo para Deploy](#passo-a-passo-para-deploy)
3. [Comandos Administrativos](#comandos-administrativos)
4. [Diferenciais Técnicos (Engenharia de Dados)](#diferenciais-técnicos)
5. [Gestão de Recursos](#gestão-de-recursos)

---

## 🔍 Visão Geral
O sistema opera através de dois componentes principais:
* **UserBot (Monitor):** Atua na "escuta passiva" de centenas de canais de promoção aos quais sua conta pessoal pertence.
* **Bot API (Notificador):** Responsável pelo envio de notificações ricas (com mídia e formatação original) para o canal de destino, garantindo que o UserBot não seja sobrecarregado.

---

## 🛠️ Passo a Passo para Deploy

### 1. Obtenção de Credenciais
Você precisará de dois conjuntos de chaves do Telegram:
1.  **App API:** Acesse [my.telegram.org](https://my.telegram.org), crie uma aplicação e obtenha seu `API_ID` e `API_HASH`.
2.  **Bot Token:** Fale com o [@BotFather](https://t.me/BotFather) e crie um novo bot para obter o `BOT_TOKEN`.

### 2. Configuração do Canal de Destino
1.  Crie um canal no Telegram (ex: `PromoF`).
2.  Adicione o seu **Bot API** (criado no BotFather) como **Administrador** do canal.
3.  Obtenha o ID do canal (ex: `-100123456789`). Insira este valor na variável `DESTINO` do seu `.env`.

### 3. Preparação das Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto seguindo o modelo abaixo:
```env
API_ID=seu_id
API_HASH=seu_hash
BOT_TOKEN=seu_token_bot
DESTINO=-100123456789
DATABASE_URL=postgresql://user:pass@db:5432/promof_db
```

### 4. Deploy via Docker Compose
No terminal do seu **Host**, execute o comando abaixo para construir a imagem e iniciar os serviços de banco de dados e aplicação:

```bash
docker compose up -d --build
```

### 5. Autenticação Inicial (First Run)
Como o UserBot simula uma conta real de usuário, você deve fornecer o código de acesso na primeira execução do container para gerar o arquivo de sessão:

* **Acompanhe os logs em tempo real**: Execute `docker logs -f promof_bot` para visualizar a solicitação de login.
* **Insira as credenciais**: Digite seu número de telefone (formato internacional) e o código enviado pelo Telegram quando solicitado no prompt do terminal.
* **Persistência**: A sessão será salva automaticamente no volume `./data`, eliminando a necessidade de novos logins em restarts futuros.

---

## 📊 Comandos Administrativos (Chat Privado)
Gerencie seus filtros e monitore a performance enviando comandos em chat privado diretamente para o UserBot:

* **`.add <termo>`**: Monitora o termo de forma irrestrita em todos os canais.
* **`.add <termo> -p <valor>`**: Define um monitoramento com teto de preço (ex: `.add notebook -p 3000`).
* **`.list`**: Exibe todos os filtros ativos, respectivos preços e a lista de palavras negativas.
* **`.remove <termo>`**: Remove permanentemente um filtro ou palavra negativa da base de dados.
* **`.stats`**: Dashboard com o total de capturas, termo mais frequente e principal fonte de dados (canal).
* **`.neg <termo>`**: Adiciona uma palavra à blacklist para ignorar promoções indesejadas.
* **`.history <termo>`**: Exibe os últimos 5 matches registrados para uma keyword específica.

---

## 💡 Diferenciais Técnicos e Otimizações
Esta solução contempla melhorias críticas de engenharia projetadas para o ambiente de **Home Lab** e alta performance:

* **Processamento em Memória (BytesIO)**: O download e re-upload de mídias originais são feitos via buffers de RAM (BytesIO), evitando escrita excessiva no SSD do Host e prevenindo condições de corrida em notificações simultâneas.
* **Proteção Anti-Loop Multinível**: Implementação de bloqueio lógico via `blacklist_chats` e verificação de `chat_id == DESTINO` para impedir que o bot monitore a própria saída.
* **Deduplicação via MD5**: Persistência de hashes das mensagens no PostgreSQL, garantindo que ofertas idênticas de fontes diferentes notifiquem o canal apenas uma vez.
* **Enriquecimento de Mensagem**: Notificações automáticas que incluem o nome do canal de origem, o item do alerta e o preço identificado no cabeçalho.



---

## ⚙️ Gestão de Recursos
Configurações de limites otimizadas para estabilidade em servidores compactos e ambientes Proxmox:

* **PostgreSQL**: Limitado a 512MB de RAM e 0.5 de CPU para garantir que o banco de dados não consuma recursos excessivos do host.
* **App PromoF**: Limitado a 1GB de RAM (para suportar buffers de mídia concorrentes) e 0.5 de CPU (processamento de Fuzzy Matching).
* **Observabilidade**: Logs centralizados com prefixo `[APP - NIVEL]` e modo `PYTHONUNBUFFERED=1`, permitindo auditoria em tempo real via terminal.