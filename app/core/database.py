import os
from dotenv import load_dotenv
from sqlalchemy import event
from sqlmodel import Session, create_engine

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else{}

engine = create_engine(DATABASE_URL, echo=True, connect_args=connect_args)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def ativar_chaves_estrangeiras(conexao, registro):
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

def get_session():
    with Session(engine) as session:
        yield session