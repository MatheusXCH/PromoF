import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Inicializa o esquema do banco de dados relacional.

    Cria todas as tabelas definidas no modelo declarativo (Base) caso elas ainda não existam 
    no banco de dados PostgreSQL configurado.
    """
    
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Gerencia a criação e o ciclo de vida de uma sessão do SQLAlchemy.

    Returns:
        Session: Uma instância de sessão configurada para interagir com o banco de dados.
    """
    
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()