import time
import uuid
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request

BLACKLIST = [
    # "127.0.0.1"
]  # Bloqueando el mismo server de trabajo :V


def register_middleware(app: FastAPI):

    @app.middleware("http")  # Registrado como un middleware HTTP global
    async def add_process_time_header(request: Request, call_next):
        """Llamar una request, recibiendo todo su contenido (url, headers, etc.) usandolo como un callback
        Permitiendo invocar otra capa como la ruta u otro middleware.
        """
        # Usamos una asincrona porque esperamos la llamada o acción siguiente
        start = time.perf_counter()
        # Esperar por la respuesta de call_next (puede ser un get, put, etc...)
        response = await call_next(request)
        # Cuando responda
        process_time = time.perf_counter() - start
        # Agregarlo a un header
        # X-Process-Time es un valor aleatorio puede ser cualquire valor
        response.headers["X-Process-Time"] = f"{process_time:.4f} s"
        return response

    # Segundo middleware
    @app.middleware("http")
    async def log_request(request: Request, call_next):
        print(f"**ENTRADA**: {request.method} \n{request.url}")
        # Resolver el request
        response = await call_next(request)
        print(f"**SALIDA**: {response.status_code}")
        return response

    # Tercer middleware: personalizar un request ID
    @app.middleware("http")
    async def add_request_id_header(request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Cuarto middleware: bloquear IPs
    @app.middleware("http")
    async def block_ip_middleware(request: Request, call_next):
        client_ip = request.client.host  # IP del cliente
        # Evaluar IPs bloqueadas
        if client_ip in BLACKLIST:
            raise HTTPException(
                status_code=403, detail="Acceso denegado a esta IP")

        # Continuar flujo natural
        return await call_next(request)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Se permitan todos los origenes '*'
        allow_credentials=True,
        allow_methods=["*"],  # All methods
        allow_headers=["*"]  # All headers
    )
    # Al permitir todo, no habra problemas
