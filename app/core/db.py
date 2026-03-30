import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

user = os.getenv("USER")
password = os.getenv("PASSWORD")
server = os.getenv("SERVER")
port = os.getenv("PORT")
database = os.getenv("DATABASE")
if not all([user, password, server, port, database]):  # No sea None o vacia
    DATABASE_URL = "sqlite:///./blog.db"
else:
    DATABASE_URL = f"postgresql+psycopg://{user}:{password}@{server}:{port}/{database}"
safe_url = DATABASE_URL.replace(password, "****") if password else DATABASE_URL
print("Conectado a:", safe_url)

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

# Conexión ======================================
# echo True => muestra el SQL ejecutado, future True => sintaxis moderna, engine_kwargs (solo para sqlite)
engine = create_engine(DATABASE_URL, echo=True, future=True, **engine_kwargs)

# Sesion ========================================
# Autoflush: False => no envía cambios hasta hacer el commit, Autocommit: False => hasta no poner commit no se realiza
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, class_=Session)


# Declarative Base ==============================
# Definir los modelos ORM como clases


class Base(DeclarativeBase):  # Esto hará de Alias
    pass


def get_db():  # Por cada endpoint me cree la sesión al ingresar, y la cierre al salir
    """conexión a la base de datos y cierre

    Yields:
        db.SessionLocal: sesion local de la instancia

    returns:
        NoneType
    """
    db = SessionLocal()  # Iniciar sesión local
    try:
        yield db  # Use la conexión y cuando termine ira al finally
    finally:
        db.close()
