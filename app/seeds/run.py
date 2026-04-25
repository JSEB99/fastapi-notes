import typer

from app.seeds.services import run_all, run_categories, run_tags, run_users

# Typer permite crear interfaces en linea de comandos

app = typer.Typer(help="Seeds: users, categories, tags")


@app.command("users")
def users():
    run_users()
    # Mostrar un echo en la terminal
    typer.echo("Usuarios cargados")


@app.command("categories")
def categories():
    run_categories()
    typer.echo("Categorias cargadas")


@app.command("tags")
def tags():
    run_tags()
    typer.echo("Etiquetas cargadas")


@app.command("all")
def all_():
    run_all()
    typer.echo("Todos los seeds creados")
