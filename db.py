from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker 
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.sqlite"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
#Передаючи {"check_same_thread": False} як connect_args, застосунок може відкривати кілька 
#з'єднань з однією і тією самою базою даних SQLite з різних потоків без помилок.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()