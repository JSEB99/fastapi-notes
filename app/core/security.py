from fastapi.security import OAuth2PasswordBearer

# Esa es la ruta que debe usar el cliente para poderse autenticar
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
