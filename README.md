# Notas FastAPI 

- El orden afecta cual se va a mostrar, si tengo dos con mismo metodo, prevalecera la que primero aparece
- **Query params:** son los que van despues de `?`
- **Path params:** son los que van en la url con `/`
- **Put:** similar a post pero busca es actualizar
- **Patch:** similar a put pero es algo *parcial*

- método para probar endpoints desde **Powershell**, en este caso con **post**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/posts" -Method POST `
>> -Headers @{"Content-Type" = "application/json"} `
>> -Body '{"title":"Cristiano Ronaldo won the WC2026","content":"The GOA7 of the hat-tricks"}'
```

# 📊 Códigos de Estado HTTP

| Código | Nombre                 | Descripción breve                                   |
| ------ | ---------------------- | --------------------------------------------------- |
| 100    | Continue               | El servidor recibió la solicitud inicial, continuar |
| 101    | Switching Protocols    | Cambio de protocolo solicitado                      |
| 200    | OK                     | Solicitud exitosa                                   |
| 201    | Created                | Recurso creado correctamente                        |
| 202    | Accepted               | Solicitud aceptada, pero no procesada aún           |
| 204    | No Content             | Sin contenido en la respuesta                       |
| 301    | Moved Permanently      | Recurso movido permanentemente                      |
| 302    | Found                  | Redirección temporal                                |
| 304    | Not Modified           | Recurso no ha cambiado                              |
| 400    | Bad Request            | Solicitud incorrecta                                |
| 401    | Unauthorized           | Falta autenticación                                 |
| 403    | Forbidden              | Acceso prohibido                                    |
| 404    | Not Found              | Recurso no encontrado                               |
| 405    | Method Not Allowed     | Método no permitido                                 |
| 408    | Request Timeout        | Tiempo de espera agotado                            |
| 409    | Conflict               | Conflicto en la solicitud                           |
| 410    | Gone                   | Recurso eliminado permanentemente                   |
| 415    | Unsupported Media Type | Tipo de contenido no soportado                      |
| 429    | Too Many Requests      | Demasiadas solicitudes                              |
| 500    | Internal Server Error  | Error interno del servidor                          |
| 501    | Not Implemented        | Funcionalidad no implementada                       |
| 502    | Bad Gateway            | Respuesta inválida de otro servidor                 |
| 503    | Service Unavailable    | Servicio no disponible                              |
| 504    | Gateway Timeout        | Tiempo de espera agotado en gateway                 |

## Status Codes

- Podemos usar los `status_code` con `HTTPException` levantando la excepción definiendo el código y el detalle
- Ademas para una respuesta correcta general la ponemos pasar como parametro en el decorador de la ruta como `status_code` indicando el código de estado que devuelve el **endpoint**

# 🔧 Verbos (Métodos) HTTP

| Método  | Descripción                                |
| ------- | ------------------------------------------ |
| GET     | Obtiene datos de un recurso                |
| POST    | Envía datos para crear un recurso          |
| PUT     | Reemplaza completamente un recurso         |
| PATCH   | Modifica parcialmente un recurso           |
| DELETE  | Elimina un recurso                         |
| HEAD    | Igual que GET pero sin cuerpo de respuesta |
| OPTIONS | Devuelve los métodos permitidos            |
| TRACE   | Devuelve la solicitud recibida (debug)     |
| CONNECT | Establece un túnel con el servidor         |


## BaseModel

- Permite poner modelos de los objetos con los que trabajemos
- Añadirles validaciones
- Añadirles metadatos 
- Podemos hacer validaciones personalizadas con **decoradores** de `@classmethod` y `@field_validator("atributo")`, el cual recibe la clase y el valor

### ResponseModel

- Basandonos en el `BaseModel` podemos usar un atributo podemos definir el objeto de la respuesta de la misma forma, en este caso este parametro se pasa en el decorador de la ruta como `response_model`. Tambien podemos especificarlo si es una lista con el tipo de valor creado y asi sucesivamente.

# Union

Union o `|` le da importancia al orden, es decir, si el primer valor del **or** cumple la condición usa ese. Esto es importante para cuando definamos valores de respuesta del modelo, ya que si el primero tiene lo mas que el segundo, pero los que le faltan son opcionales seguira usando el primero.

Esto se evidencia en el código cuando usamos:

```Python
class PostBase(BaseModel):
    title: str
    content: str | None = "Contenido no disponible"

class PostPublic(PostBase):
    id: int  # Añado lo que hace falta el resto lo heredo


class PostSummary(BaseModel):
    id: int
    title: str
```

Donde si en un `response_model=PostPublic | PostSummary` siempre usará el primero asi devolvamos solo `id` y `title`. Esto debido a que el primero el `content` es opcional, devolviendonos todos los atributos id, titulo y contenido *(nunca evaluaría PostSummary)*. La solución es invertir el orden de evaluación del **or**. Entonces validará primero `PostSummary` y si este tiene solo `id` y `title` devolvera esa *clase*, y si este tiene id, titulo y contenido devolverá `PostPublic` haciendo que se evalúe correctamente el criterio de las dos clases de respuesta para este caso.

*Nota: importante tener en cuenta el orden, ya que se evalua de izquierda a derecha con los OR*

# Path y Query

Son usados para agregarle validaciones adicionales a los parametros enviados en el **endpoint**.
- Query se usa con `Annotated`

# Paginación, Offset

- Mediante parametros query podemos filtrar la cantidad de datos, el orden y segun que valor tomaremos el orden de los datos a mostrar haciendo mas optima la carga sin tener que cargar todos los datos.

# Multiples parametros

- Recibe una lista de varios elementos

# Deprecated

- Atributo en Query o Path `deprecated` que es booleano