from typing import Annotated, Literal, Optional
from fastapi import FastAPI, Query, HTTPException, Path, status, Depends
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
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


@app.post("/posts", response_model=PostPublic, response_description="Post creado (OK)", status_code=status.HTTP_201_CREATED)
# ... elipsis -> obligatorio | Le pasamos la sesion
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    # author_obj = None
    # if post.author:
    #     author_obj = db.execute(
    #         select(AuthorORM).where(AuthorORM.email == post.author.email)
    #     ).scalar_one_or_none()
    #     if not author_obj:
    #         author_obj = AuthorORM(
    #             name=post.author.name,
    #             email=post.author.email
    #         )
    #         # Agregr el autor
    #         db.add(author_obj)
    #         # Asignar el ID antes del commit
    #         db.flush()
    new_post = PostORM(
        title=post.title, content=post.content, author=author_obj)

    for tag in post.tags:
        tag_obj = db.execute(
            select(TagORM).where(TagORM.name.ilike(tag.name))
        ).scalar_one_or_none()
        if not tag_obj:
            tag_obj = TagORM(name=tag.name)
            # Agrego
            db.add(tag_obj)
            # Genero ID
            db.flush()
        # Voy agregando 1 a 1 cada tag
        new_post.tags.append(tag_obj)
    try:
        # Marcar la inserción
        db.add(new_post)
        # Confirmar (Commit)
        db.commit()
        # Traer los valores finales (id, created_at)
        db.refresh(new_post)
        return new_post
    except IntegrityError as e:
        db.rollback()  # Desaga la operación frente a error
        raise HTTPException(status_code=409, detail="El título ya existe")
    except SQLAlchemyError:
        # Desaga la operación frente a error
        db.rollback()
        # Notificar error
        raise HTTPException(status_code=500, detail="Error al crear el Post")


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
