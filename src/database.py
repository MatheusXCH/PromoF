import os
from sqlalchemy import create_engine # Removido o 'create_all' daqui
from sqlalchemy.orm import sessionmaker
from models import Base # Importando o Base que contém o metadata

DATABASE_URL = os.getenv('DATABASE_URL')

# Criar o engine de conexão
engine = create_engine(DATABASE_URL)

# Criar a fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # O create_all é chamado a partir do metadata do Base
    # Ele verifica quais tabelas em models.py ainda não existem e as cria
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()