import typer
from rich import print
from rich.prompt import Prompt

from salman.chatbot import bot

app = typer.Typer()


@app.command()
def prompt():
    while True:
        q = Prompt.ask(">")
        if q in ["exit", "quit"]:
            break
        resp = bot.run(q)
        print(resp)
