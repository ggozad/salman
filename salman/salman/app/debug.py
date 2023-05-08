from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import TextLog


class DebugLog(Widget):
    def write(self, text, format="text"):
        syntax = Syntax(
            text,
            format,
            indent_guides=True,
        )
        text_log: TextLog = self.query_one("TextLog")
        text_log.write(syntax, expand=True)

    def compose(self) -> ComposeResult:
        yield TextLog(highlight=True, markup=True)
