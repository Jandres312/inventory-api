
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

# URL de conexión a PostgreSQL (viene del .env)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/inventory"
)

# Motor de conexión: es el "puente" entre Python y la base de datos
engine = create_engine(DATABASE_URL)

# SessionLocal: cada vez que necesitemos hablar con la DB, abrimos una sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: clase padre de la que heredarán todos nuestros modelos (tablas)
Base = declarative_base()


# Función generadora que abre y cierra la conexión automáticamente
def get_db():
    db = SessionLocal()
    try:
        yield db  # "presta" la conexión mientras se usa
    finally:
        db.close()  # siempre la cierra al terminar
        