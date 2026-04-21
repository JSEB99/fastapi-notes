import os


class Settings():
    JWT_SECRET: str = os.getenv("SECRET_KEY", "change-me-in-prod")
    # Recomendado / Estandar (otras opciones RS256, etc.)
    JWT_ALG: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
