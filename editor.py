import string
from copy import copy
from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import List

from pygments.lexers import get_lexer_by_name
from rich import get_console
from rich.console import RenderableType
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from textual import events
from textual.app import App
from textual.reactive import Reactive
from textual.view import View
from textual.widget import Widget
from textual.widgets import Header, ScrollView, Footer

console = get_console()

TABSIZE: int = 4
NUMBERS: str = ''.join((str(i) for i in range(9)))


class Move(str, Enum):
    right = "right"
    left = "left"
    up = "up"
    down = "down"


@dataclass
class Position:
    line: int
    row: int

    def __repr__(self):
        return f"({self.line}, {self.row})"


@dataclass
class Cursor:
    position: Position

    @classmethod
    def end_of_text(cls, text: List[str]) -> "Cursor":
        num_lines = len(text) - 1
        row = len(text[-1])

        return Cursor(Position(num_lines, row))

    @classmethod
    def begin_of_text(cls, text: List[str] = None) -> "Cursor":
        return Cursor(Position(0, 0))

    def __repr__(self):
        return "│"


class Action(str, Enum):
    insert = "insert"
    vim = "vim"

    def __repr__(self):
        return f"--{self.value}--"


class Editor(Widget):
    typing = Reactive(False)
    focused = Reactive(False)
    action = Reactive(Action.insert)

    def __init__(self, text: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.segments = text.split('\n')

        self.cursor = Cursor.end_of_text(self.segments)

        characters = (
                string.ascii_lowercase
                + string.ascii_uppercase
                + "!\"#$%&'()*+-/:;<=>?@[\\]^_`{|}~"
                + NUMBERS
        )
        for char in characters:
            setattr(self, f"key_{char}", partial(self._write, char))

    def footer(self):
        footer_table = Table.grid(padding=(2, 2), expand=True, )
        footer_table.style = "black on white"
        footer_table.add_column(justify="left", ratio=0, width=8)
        # footer_table.add_column("title", justify="center", ratio=1)
        footer_table.add_column("cursor", justify="right", width=8)
        footer_table.add_row(
            str(self.action), str(self.cursor.position), style="black on white"
        )

        return footer_table

    def render(self) -> RenderableType:
        # insert marker at cursor position
        text = copy(self.segments)
        current_line = text[self.cursor.position.line]
        text[self.cursor.position.line] = current_line[:self.cursor.position.row] + str(self.cursor) + current_line[
                                                                                                       self.cursor.position.row:]

        syntax = Syntax(
            '\n'.join(text),
            lexer=get_lexer_by_name("md"),
            line_range=(1, 100),
            tab_size=TABSIZE,
            indent_guides=True,
            line_numbers=True,
            word_wrap=True,
            theme="monokai",
        )

        editor_grid = Table.grid()
        editor_grid.add_column()
        editor_grid.add_row(syntax)
        editor_grid.add_row(self.footer())

        panel_title = Text("Editor", style="bold" if self.focused else None)
        return Panel(editor_grid, title=panel_title, border_style="white" if self.focused else "gray")

    async def on_key(self, event: events.Key) -> None:
        if event.key == "ctrl+h":
            await self._delete()
        elif event.key == "ctrl+i":
            await self.write_tab()
        elif event.key in list(Move):
            await self.move_cursor(Move(event.key))
        elif event.key in (".", ",", " "):
            await self._write(event.key)
        else:
            await self.dispatch_key(event)
        self.typing = not self.typing

    async def key_enter(self):
        current_line = self.segments[self.cursor.position.line]
        if self.cursor.position.line < len(self.segments) - 1:
            left, right = current_line[:self.cursor.position.row], current_line[self.cursor.position.row:]
            self.segments = self.segments[:self.cursor.position.line] + [left] + [right] + self.segments[
                                                                                           self.cursor.position.line + 1:]
        else:
            self.segments.append('')
        self.cursor.position.line += 1
        self.cursor.position.row = 0

        if current_line.strip():
            if current_line.strip()[0] in list(NUMBERS) + ['-', '+', '*'] and len(current_line.strip()) > 1:
                if current_line.strip()[0] in list(NUMBERS) and (len(current_line.strip()) > 1 and current_line.strip()[1] == '.'):
                    await self._write(current_line.strip()[0] + ". ")
                else:
                    await self._write(current_line.strip()[0] + " ")

    async def write_tab(self):
        await self._write(' ' * TABSIZE)
        #self.cursor.position.row += TABSIZE

    async def _write_auto_complete(self, text: str):
        completion = {'[': ']',
                      '(': ')',
                      '"': '"',
                      '\'': '\'',
                      '`': '`'
                      }
        if text in completion:
            await self._write(completion[text], auto_complete=False)
            self.cursor.position.row -= 1

    async def _write(self, text: str, auto_complete: bool = True):
        current_line = self.segments[self.cursor.position.line]
        current_line = current_line[:self.cursor.position.row] + text + current_line[self.cursor.position.row:]
        self.segments[self.cursor.position.line] = current_line
        self.cursor.position.row += len(text)

        if auto_complete:
            await self._write_auto_complete(text)
        # await self.move_cursor(Move.right)

    async def _delete(self):
        current_line = self.segments[self.cursor.position.line]
        if current_line == '':
            if self.cursor.position.line > 0:
                self.segments = self.segments[:-1]
                self.cursor = Cursor.end_of_text(self.segments)
        elif self.cursor.position.row == 0:
            previous_line = len(self.segments[self.cursor.position.line - 1])
            self.segments[self.cursor.position.line - 1] += current_line
            self.segments[self.cursor.position.line:] = self.segments[self.cursor.position.line + 1:]
            self.cursor.position.line -= 1
            self.cursor.position.row = previous_line

        else:
            await self.move_cursor(Move.left)
            current_line = current_line[:self.cursor.position.row] + current_line[self.cursor.position.row + 1:]
            self.segments[self.cursor.position.line] = current_line

    async def move_cursor(self, move: Move):
        if move == Move.left:
            await self.move_cursor_left()
        elif move == Move.right:
            await self.move_cursor_right()
        elif move == Move.up:
            if self.cursor.position.line > 0:
                self.cursor.position.line -= 1
            else:
                self.cursor = Cursor.begin_of_text()
        elif move == move.down:
            if self.cursor.position.line < len(self.segments) - 1:
                self.cursor.position.line += 1
                self.cursor.position.row = min(len(self.segments[self.cursor.position.line]), self.cursor.position.row)

    async def move_cursor_left(self):
        if self.cursor.position.row > 0:
            self.cursor.position.row -= 1
        else:
            self.cursor.position.line -= 1
            self.cursor.position.row = len(self.segments[self.cursor.position.line])

    async def move_cursor_right(self):
        current_line = self.segments[self.cursor.position.line]
        if self.cursor.position.row < len(current_line):
            self.cursor.position.row += 1
        else:
            if self.cursor.position.line < len(self.segments):
                await self.move_cursor(Move.down)

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
            self.editor = Editor(text=example_md, name="editor")
            self.body = ScrollView(self.editor, )

            await self.view.dock(Header(), edge="top")
            await self.view.dock(Footer(), edge="bottom")
            await self.view.dock(self.editor, edge="left")

            await self.editor.focus()


    EditorApp.run(log=f"textual.log")
