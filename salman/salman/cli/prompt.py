import typer
from rich import print
from rich.prompt import Prompt

from salman.llm import get_agent, get_chain

app = typer.Typer()


@app.command()
def chain():
    chain = get_chain()
    while True:
        q = Prompt.ask(">")
        if q in ["exit", "quit"]:
            break
        resp = chain.run(q)
        print(resp)


@app.command()
def agent():
    agent = get_agent()
    while True:
        q = Prompt.ask(">")
        if q in ["exit", "quit"]:
            break
        resp = agent.run(q)
        print(resp)


if __name__ == "__main__":
    app()
