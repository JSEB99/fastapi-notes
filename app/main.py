from fastapi import FastAPI
from app.core.db import Base, engine
from dotenv import load_dotenv
from app.api.v1.posts.router import router as post_router  # router de posts
from app.api.v1.auth.router import router as auth_router  # router de auth
# Servidor de la DB
# Sino existe crea una base de datos sqlite
# PostgreSQL variables
load_dotenv()


# Clases de los modelos


def create_app() -> FastAPI:
    """Crear instancia de FastAPI"""
    app = FastAPI(title="Mini Blog")

    # Metodo para crear las tablas en caso de que no existan
    # Accedemos a la conexión y creamos las tablas (recomendado en dev)
    # En Prod se usan migraciones
    Base.metadata.create_all(bind=engine)  # Solo Dev

    # Montar el Router de Auth =======================================
    app.include_router(auth_router, prefix="/api/v1")
    # le añadimos prefijo para que pueda acceder a toda la ruta
    # del login

    # Montar el Router de Post =======================================
    app.include_router(post_router)

    # Rutas personalizadas aparte ====================================
    @app.get("/")  # ejemplo: bienvenida al Blog
    def welcome():
        return {"Welcome to MiniBlog App"}
    return app


app = create_app()
