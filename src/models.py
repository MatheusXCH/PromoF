from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Keyword(Base):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True)
    word = Column(String, unique=True, nullable=False)
    max_price = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class MessageLog(Base):
    """Armazena o hash das mensagens para evitar duplicatas mesmo após restart"""
    __tablename__ = 'message_logs'
    id = Column(Integer, primary_key=True)
    msg_hash = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class NegativeKeyword(Base):
    __tablename__ = 'negative_keywords'
    id = Column(Integer, primary_key=True)
    word = Column(String, unique=True, nullable=False)

class MatchLog(Base):
    __tablename__ = 'match_logs'
    id = Column(Integer, primary_key=True)
    keyword_id = Column(Integer, ForeignKey('keywords.id', ondelete='CASCADE'))
    channel_id = Column(String)
    content_preview = Column(String)
    price_extracted = Column(Float, nullable=True)
    is_fuzzy = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())