import os
from dataclasses import dataclass

from rich.console import RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from textual import events
from textual.app import App
from textual.widget import Widget
from textual.widgets import Header, Footer

from editor import Editor
from file import new_file

# TODO
# 1. switching focus with tab
# 2. writing white space
# 3. toggle side bar
# 4. navigation with arrow keys, widget?
# 5. vim key bindings

ROOT = "./"


@dataclass
class Position:
    line: int
    row: int


@dataclass
class Cursor:
    position: Position

    def __repr__(self):
        return "█"


def get_cursor(content: str):
    lines = content.split("\n")
    num_lines = len(lines)
    row = len(lines[-1])

    return Cursor(Position(num_lines, row))


def write_at_position(content: str, new_content: str, position: Position) -> str:
    """

    """
    lines = content.split("\n")
    current_line = lines[position.line]

    head, tail = current_line[:position.row], current_line[position.row]
    current_line = head + new_content + tail
    content = '\n'.join(lines[:position.line - 1] + [current_line] + lines[position.line:])
    return content


class CodeViewer(Widget):
    def __init__(self, text: str, *args, **kwargs):
        super(CodeViewer, self).__init__(*args, **kwargs)
        self.text = text

    def on_mount(self):
        self.set_interval(1, self.refresh)

    def render(self) -> RenderableType:
        return Panel(Markdown(self.text), title="Markdown Preview")


class NoteApp(App):
    async def on_load(self) -> None:

        # Bind our basic keys
        await self.bind("ctrl+b", "view.toggle('editor')", "Toggle editor")
        await self.bind("ctrl+v", "view.toggle('viewer')", "Toggle code viewer")
        await self.bind("ctrl+t", "view.toggle('tree)", "Toggle tree view")
        await self.bind("ctrl+q", "quit", "Quit")
        await self.bind("ctrl+s", "save", "Save")
        await self.bind("ctrl+n", "new", "New")

    async def on_mount(self) -> None:
        self.file = new_file()
        self.editor = Editor(self.file.content, name="editor")
        self.monitor = CodeViewer(self.editor.text, name="viewer")

        # Dock our widgets
        await self.view.dock(Header(), edge="top")
        await self.view.dock(Footer(), edge="bottom")

        await self.view.dock(self.editor,self.monitor, edge="left")

        await self.editor.focus()

    async def action_save(self) -> None:
        self.file.content = self.editor.text
        fname = self.file.fname.replace("/", "-")

        with open(os.path.join(ROOT, fname), "w") as f:
            f.writelines(self.editor.text)

        self.app.sub_title = f"{self.file.fname}"

    async def action_new(self):
        self.file = new_file()
        self.editor = Editor(self.file.content, name="editor")
        self.monitor = CodeViewer(self.editor.text, name="viewer")

    async def on_key(self, event: events.Key) -> None:
        self.monitor.text = self.editor.text




# Run our app class
NoteApp.run(title="Code Viewer", log="textual.log")
