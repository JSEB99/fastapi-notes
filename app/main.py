from typing import Annotated, Literal, Optional
from fastapi import FastAPI, Query, HTTPException, Path, status, Depends
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload, joinedload
from dotenv import load_dotenv

# Servidor de la DB
# Sino existe crea una base de datos sqlite
# PostgreSQL variables
load_dotenv()


# Clases de los modelos


# Metodo para crear las tablas en caso de que no existan
# Accedemos a la conexión y creamos las tablas (recomendado en dev)
# En Prod se usan migraciones
Base.metadata.create_all(bind=engine)


app = FastAPI(title="Mini Blog")


@app.get("/")
def home():
    return {'message': 'Bienvenidos a Mini Blog de JSEBM99'}

# exclude_none, me excluya los valores que no le envío al endpoint


@app.put("/posts/{post_id}", response_model=PostPublic, response_description="Post actualizado", response_model_exclude_none=True)
def update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db)):

    post = db.get(PostORM, post_id)

    if not post:  # Sino lo encuentra
        raise HTTPException(status_code=404, detail="Post no encontrado")

    payload = data.model_dump(exclude_unset=True)

    for key, value in payload.items():
        # Reasignación de valor
        setattr(post, key, value)

    db.commit()
    db.refresh(post)

    return PostPublic.model_validate(post, from_attributes=True)


# 204 => Salio bien, pero no regresa contenido
@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.get(PostORM, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    # Alternativa
    # sqlalchemy import delete
    # del_query = delete(PostORM).where(PostORM.id == post_id)
    # db.execute(del_query)

    db.delete(post)
    db.delete(post)
    db.commit()
    return
