import os
from fastapi import FastAPI
from app.core.db import Base, engine
from dotenv import load_dotenv
from app.api.v1.posts.router import router as post_router  # router de posts
from app.api.v1.auth.router import router as auth_router  # router de auth
from app.api.v1.uploads.router import router as upload_router  # router de uploads
from app.api.v1.tags.router import router as tag_router  # router de tags
from app.api.v1.categories.router import router as category_router  # router de category
from fastapi.staticfiles import StaticFiles
# Servidor de la DB
# Sino existe crea una base de datos sqlite
# PostgreSQL variables
load_dotenv()


# Ruta de media
MEDIA_DIR = "app/media"

# API descripción
description = """
### API de Gestión de Notas
Esta API es un proyecto educativo diseñado para demostrar las capacidades de **FastAPI** en el desarrollo de servicios backend modernos.

#### Características principales:
* **CRUD Completo:** Gestión total de notas (Crear, Leer, Actualizar y Eliminar).
* **Validación de Datos:** Uso de esquemas Pydantic para garantizar la integridad de la información.
* **Documentación Automática:** Interfaz interactiva disponible en `/docs` para pruebas en tiempo real.
* **Rendimiento:** Implementación asíncrona para un manejo eficiente de peticiones.

Ideal como base para aprender arquitectura REST y tipado estático en Python.

> Fuente: https://www.udemy.com/course/fastapi-apis-eficientes/
"""

# Clases de los modelos


def create_app() -> FastAPI:
    """Crear instancia de FastAPI"""
    app = FastAPI(
        title="Mini Blog",
        description=description,
        contact={
            "name": "Sebastian Mora",
            "url": "https://www.linkedin.com/in/jsebastianm/",
            "email": "sebastian.mt99@gmail.com"},
        swagger_ui_parameters={"persistAuthorization": True}
    )

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

    # Montar el Router de Tags ======================================
    app.include_router(tag_router)

    # Montar Router de Uploads ======================================
    app.include_router(upload_router)

    # Montar Router de Category =====================================
    app.include_router(category_router)

    os.makedirs(MEDIA_DIR, exist_ok=True)  # Creala sino existe
    # Montamos la URL para acceso de los archivos =====================
    app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

    # Rutas personalizadas aparte ====================================
    @app.get("/")  # ejemplo: bienvenida al Blog
    def welcome():
        return {"Welcome to MiniBlog App"}
    return app


app = create_app()
