from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Input

from salman.app.chat import Author, ChatItem
from salman.app.prompt import PromptWidget


class Salman(App):
    """Salman the command line personal assistant."""

    CSS_PATH = "salman.css"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Event handler called when an input is submitted."""
        container = self.query_one("#container")
        item = ChatItem(text=event.value, author=Author.USER)
        container.mount(item)
        item.scroll_visible()
        self.query_one("#promptInput").value = ""

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Container(id="container"):
            yield ChatItem(text="Hello, how can I help?", author=Author.SALMAN)
        yield PromptWidget()
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark
