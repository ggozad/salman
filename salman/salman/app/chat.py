from enum import Enum

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Static


class Author(Enum):
    USER = "me"
    SALMAN = "salman"


class ChatItem(Static):
    def __init__(self, text="", author=Author.USER, **kwargs):
        super().__init__(**kwargs)
        self.author = author
        self.text = text

    text: str = reactive("")
    author: Author = Author.USER

    def compose(self) -> ComposeResult:
        """A chat item."""
        with Horizontal(classes=f"{self.author.value} chatItem"):
            yield Static(self.author.value, classes="author")
            yield Static(self.text, classes="text")
