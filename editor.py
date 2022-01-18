import string
from functools import partial

from pygments.lexers import get_lexer_by_name
from rich import get_console
from rich.panel import Panel
from rich.syntax import Syntax
from textual import events
from textual.app import App
from textual.reactive import Reactive
from textual.view import View
from textual.widget import Widget
from textual.widgets import Header, ScrollView, Footer

console = get_console()


class Editor(Widget):
    typing = Reactive(False)
    focused = Reactive(False)

    def __init__(self, text: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        characters = (
            string.ascii_lowercase
            + string.ascii_uppercase
            + "!\"#$%&'()*+-/:;<=>?@[\\]^_`{|}~"
        )
        for char in characters:
            setattr(self, f"key_{char}", partial(self._write, char))

    def render(self) -> ScrollView:
        syntax = Syntax(
            self.text + '█',
            lexer=get_lexer_by_name("md"),
            line_numbers=True,
            word_wrap=True,
            indent_guides=True,
            theme="monokai",
        )
        return Panel(
            syntax, title="Editor", border_style="white" if self.focused else "gray"
        )

    async def on_key(self, event: events.Key) -> None:
        if event.key == "ctrl+h":
            await self._delete()
        elif event.key in (".", ",", " "):
            await self._write(event.key)
        else:
            await self.dispatch_key(event)
        self.typing = not self.typing

    async def key_enter(self):
        await self._write("\n")

    async def _write(self, text: str):
        self.text += text

    async def _delete(self):
        self.text = self.text[:-1]

    async def focus(self):
        self.focused = not self.focused
        await super().focus()


if __name__ == "__main__":
    example_md = """Start by entering a title
===
Happy hacking :)
"""

    class EditorApp(App):
        """Demonstrates custom widgets"""

        async def on_load(self):
            await self.bind("ctrl+q", "quit", "Quit")

        async def on_mount(self) -> None:
            self.editor = Editor(example_md, name="editor")
            await self.view.dock(Header(), self.editor, Footer(), edge="top")
            await self.editor.focus()

    EditorApp.run(log=f"textual.log")
