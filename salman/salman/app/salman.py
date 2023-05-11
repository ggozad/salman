import asyncio
import json

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Input

from salman.app.chat import Author, ChatItem
from salman.app.debug import DebugLog
from salman.app.prompt import PromptWidget
from salman.llm.anthropic import SalmanAI


class Salman(App):
    """Salman the command line personal assistant."""

    CSS_PATH = "salman.css"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("l", "toggle_log", "Show/Hide debug log"),
    ]

    assistant = SalmanAI()

    async def get_llm_reponse(self, text: str) -> str:
        """Get a response from the LLM chain."""
        await asyncio.sleep(0.1)

        response = await self.assistant.chat(text)
        self.write_log(json.dumps(response), format="json")
        for fact in response.get("facts", []):
            text = f"💡 TIL: {fact.get('subject')} {fact.get('predicate')} {fact.get('object')}"
            item = ChatItem(text=text, author=Author.SALMAN_THOUGHT)
            container = self.query_one("#container")
            container.mount(item)
            item.scroll_visible()
        if response.get("response"):
            item = ChatItem(text=response.get("response"), author=Author.SALMAN)
            container = self.query_one("#container")
            container.mount(item)
            item.scroll_visible()
        prompt = self.query_one("#promptInput")
        prompt.disabled = False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Event handler called when an input is submitted."""
        container = self.query_one("#container")
        item = ChatItem(text=event.value, author=Author.USER)
        container.mount(item)
        item.scroll_visible()
        prompt = self.query_one("#promptInput")
        prompt.value = ""
        prompt.disabled = True
        asyncio.create_task(self.get_llm_reponse(event.value))

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield DebugLog(id="debug")
        with Container(id="container"):
            yield ChatItem(text="Hello, how can I help?", author=Author.SALMAN)
        yield PromptWidget()
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_toggle_log(self) -> None:
        """An action to toggle the debug log."""
        log = self.query_one("#debug")
        log.has_class("show")
        if log.has_class("show"):
            log.remove_class("show")
        else:
            log.add_class("show")

    def write_log(self, text: str, format="text") -> None:
        """Log a message to the debug log."""
        text_log: DebugLog = self.query_one("#debug")
        text_log.write(text, format=format)
