import typer

from salman.app.salman import Salman

app = typer.Typer()


@app.command()
def salman():
    app = Salman()
    app.run()


if __name__ == "__main__":
    app()
