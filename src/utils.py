import re
from thefuzz import fuzz

PRICE_REGEX = r'(?:R\$|r\$)\s?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'

def extract_price(text):
    """Extrai o primeiro valor em R$ encontrado no texto."""
    match = re.search(PRICE_REGEX, text)
    if match:
        price_str = match.group(1).replace('.', '').replace(',', '.')
        try:
            return float(price_str)
        except ValueError:
            return None
    return None

def is_fuzzy_match(keyword_word, text_words, threshold=85):
    """Verifica similaridade entre a keyword e as palavras do texto."""
    for tw in text_words:
        if fuzz.ratio(keyword_word, tw) >= threshold:
            return True
    return False

# No arquivo src/utils.py
STORES_MAP = {
    'amazon.com': '📦 AMAZON',
    'mercadolivre.com': '🤝 MERCADO LIVRE',
    'magazineluiza.com': '🛒 MAGALU',
    'kabum.com': '💥 KABUM',
    'casasbahia.com': '🏠 CASAS BAHIA',
    'ali-express.com': '🌏 ALIEXPRESS'
}

def identify_store(text):
    """Identifica a loja através de links na mensagem."""
    for domain, tag in STORES_MAP.items():
        if domain in text.lower():
            return tag
    return "🛍️ OUTRA LOJA"