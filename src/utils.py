import logging
import sys
import re
from thefuzz import fuzz

PRICE_REGEX = r'(?:R\$|r\$)\s?(\d+(?:[\.,]\d+)*)'

def extract_price(text):
    """
    Identifica e converte o primeiro valor monetário brasileiro (R$) presente em um texto.

    Processa a string utilizando regex para capturar valores, removendo separadores de 
    milhar e ajustando decimais para o formato float padrão do Python. Suporta valores 
    contínuos sem pontuação (ex: 2564).

    Args:
        text (str): Texto bruto da mensagem de promoção.

    Returns:
        float | None: O valor convertido em float ou None se nenhum valor for identificado.
    """
    
    match = re.search(PRICE_REGEX, text)
    if match:
        price_str = match.group(1).replace('.', '').replace(',', '.')
        try:
            return float(price_str)
        except ValueError:
            return None
    return None

def is_fuzzy_match(keyword_word, text_words, threshold=85):
    """
    Realiza uma comparação de similaridade entre strings para capturar variações léxicas.

    Utiliza o algoritmo de Levenshtein para determinar se uma palavra do texto é 
    suficientemente similar à palavra-chave desejada.

    Args:
        keyword_word (str): A palavra-chave alvo.
        text_words (list[str]): Lista de palavras extraídas da mensagem original.
        threshold (int, optional): Percentual de similaridade mínima (0-100). Defaults to 85.

    Returns:
        bool: True se houver um match aproximado dentro do limite estabelecido.
    """
    
    for tw in text_words:
        if fuzz.ratio(keyword_word, tw) >= threshold:
            return True
    return False

STORES_MAP = {
    'amazon.com': '📦 AMAZON',
    'mercadolivre.com': '🤝 MERCADO LIVRE',
    'magazineluiza.com': '🛒 MAGALU',
    'kabum.com': '💥 KABUM',
    'casasbahia.com': '🏠 CASAS BAHIA',
    'ali-express.com': '🌏 ALIEXPRESS'
}

def identify_store(text):
    """
    Identifica a loja de origem com base na assinatura de domínios em links.

    Args:
        text (str): Texto contendo links ou referências à loja.

    Returns:
        str: Nome formatado da loja (tag) ou 'OUTRA LOJA' por padrão.
    """
    
    for domain, tag in STORES_MAP.items():
        if domain in text.lower():
            return tag
    return "🛍️ OUTRA LOJA"

def setup_logging():
    """
    Configura o motor de logs da aplicação para saída padronizada.

    Define o formato de mensagem como '[APP - NIVEL]', nível INFO e direciona a 
    saída para sys.stdout, garantindo compatibilidade com o buffering do Docker.
    """
    
    LOG_FORMAT = "[APP - %(levelname)s] %(asctime)s - %(name)s - %(message)s"
    
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.getLogger('telethon').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)