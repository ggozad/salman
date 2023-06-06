import asyncio
import json

from anthropic import AI_PROMPT, HUMAN_PROMPT
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Input

from salman.app.chat import Author, ChatItem, FactItem
from salman.app.debug import DebugLog
from salman.app.prompt import PromptWidget
from salman.llm.agents import search_internet, search_kb
from salman.llm.bot import SalmanAI
from salman.logging import salman as logger

SYSTEM_PROMPT = "\n\nSystem:"


def handle_exception(loop, context):
    # context["message"] will always be there; but context["exception"] may not
    msg = context.get("exception", context["message"])
    logger.error(f"Caught exception: {msg}")


class Salman(App):
    """Salman the command line personal assistant."""

    CSS_PATH = "salman.css"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("l", "toggle_log", "Show/Hide debug log"),
    ]
    history: list[str] = []
    assistant = SalmanAI()

    def on_mount(self):
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handle_exception)

    async def get_llm_reponse(self, text: str) -> str:
        """Get a response from the LLM chain."""
        await asyncio.sleep(0.1)

        response = await self.assistant.chat(text, history=self.history)
        self.history.append(f"{HUMAN_PROMPT}{text}")
        self.history.append(f'{AI_PROMPT}{response.get("response")}')
        self.write_log(json.dumps(response), format="json")
        for fact in response.get("facts", []):
            item = FactItem(fact)
            container = self.query_one("#container")
            container.mount(item)
            item.scroll_visible()
        if response.get("text_response"):
            item = ChatItem(text=response.get("text_response"), author=Author.SALMAN)
            container = self.query_one("#container")
            container.mount(item)
            item.scroll_visible()

        # See if we need agents
        agent_steps = response.get("agent_steps")
        if agent_steps:
            container = self.query_one("#container")
            info = ChatItem(
                text="🕵  Searching my knowledge base and the internet…",
                author=Author.SALMAN,
            )
            container.mount(info)
            info.scroll_visible()
            kb_search = agent_steps.get("kb_search")

            if kb_search:
                kb_facts = "\n".join(await search_kb(kb_search))
                self.write_log(json.dumps(kb_facts), format="json")
                if kb_facts:
                    self.history.append(
                        f"{SYSTEM_PROMPT}Found the following facts in the knowledge base about {kb_search}:\n{kb_facts}"
                    )
                else:
                    self.history.append(
                        f"{SYSTEM_PROMPT}No answers found in the knowledge base. Will not look again for {kb_search}."
                    )
            internet_search = agent_steps.get("internet_search")
            if internet_search:
                search_answer = await search_internet(internet_search)
                self.write_log(json.dumps(search_answer), format="json")
                if search_answer:
                    url = search_answer.get("url")
                    title = search_answer.get("title")
                    answer = search_answer.get("answer")
                    self.history.append(
                        f"""{SYSTEM_PROMPT}Found the following searching on the internet about {internet_search}:
                        Website: {title} - {url}
                        Answer: {answer}"""
                    )
                else:
                    self.history.append(
                        f"{SYSTEM_PROMPT}No answers found while searching the internet. Will not look again about {internet_search}."
                    )
            await self.get_llm_reponse(text)
            info.remove()

        else:
            # There are no things to search, assume we can reset the history,
            # so we can start a new conversation
            self.history = []
            prompt = self.query_one("#promptInput")
            prompt.disabled = False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Event handler called when an input is submitted."""
        container = self.query_one("#container")
        asyncio.create_task(self.get_llm_reponse(event.value))
        item = ChatItem(text=event.value, author=Author.USER)
        container.mount(item)
        item.scroll_visible()
        prompt = self.query_one("#promptInput")
        prompt.value = ""
        prompt.disabled = True

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
