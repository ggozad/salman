from enum import Enum

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Static

from salman.graph.triples import Node, create_semantic_triple


class Author(Enum):
    USER = "me"
    SALMAN = "salman"
    SALMAN_THOUGHT = "salman's thought"


class ChatItem(Static):
    text: str = reactive("")
    author: Author = Author.USER

    def __init__(self, text="", author=Author.USER, **kwargs):
        super().__init__(**kwargs)
        self.author = author
        self.text = text

    def compose(self) -> ComposeResult:
        """A chat item."""
        with Horizontal(classes=f"{self.author.name} chatItem"):
            yield Static(self.author.value, classes="author")
            yield Static(self.text, classes="text")


class FactItem(Static):
    subject: str
    predicate: str
    object: str
    text: str

    def __init__(self, fact: dict()):
        super().__init__()
        self.subject = fact.get("subject")
        self.predicate = fact.get("predicate")
        self.object = fact.get("object")
        self.text = f"💡 TIL: {self.subject} {self.predicate} {self.object}"

    @on(Button.Pressed, ".discardButton")
    async def discard(self) -> None:
        self.remove()

    @on(Button.Pressed, ".rememberButton")
    async def remember(self) -> None:
        # Persist the fact in the database
        create_semantic_triple(
            Node(name=self.subject),
            self.predicate,
            Node(name=self.object),
        )
        self.remove()

    def compose(self) -> ComposeResult:
        """A chat item."""
        with Horizontal(classes=f"{Author.SALMAN_THOUGHT.name} chatItem"):
            yield Static(Author.SALMAN_THOUGHT.value, classes="author")
            yield Static(self.text, classes="text")
            with Horizontal(classes="buttons"):
                yield Button(
                    label="Remember", classes="button rememberButton", variant="default"
                )
                yield Button(
                    label="Discard", classes="button discardButton", variant="error"
                )
