import os
import sys
from dataclasses import dataclass

from rich.console import RenderableType
from rich.traceback import Traceback
from textual import events
from textual.app import App
from textual.widgets import Header, Footer, DirectoryTree, ScrollView, FileClick

from code_viewer import CodeViewer
from editor import Editor
from file import new_file, load_file

NOTETERM_DIR: str = os.environ.get('NOTETERM_PATH', os.path.dirname(os.path.realpath(__file__)))


# TODO
# 1. switching focus with tab
# 3. toggle side bar
#   - with `ctrl+o` toggle side bar and browse through argument location
# 4. navigation with arrow keys, widget?
# 5. vim key bindings

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


class NoteApp(App):
    async def on_load(self) -> None:

        # Bind our basic keys
        await self.bind("ctrl+b", "view.toggle('editor')", "Toggle editor")
        await self.bind("ctrl+v", "view.toggle('viewer')", "Toggle code viewer")
        await self.bind("ctrl+b", "view.toggle('sidebar')", "Toggle sidebar")
        await self.bind("ctrl+q", "quit", "Quit")
        await self.bind("ctrl+s", "save", "Save")
        await self.bind("ctrl+n", "new", "New")

        # Get path to show
        try:
            self.path = sys.argv[1]
        except IndexError:
            self.path = os.path.abspath(
                os.path.join(NOTETERM_DIR)
            )

    async def on_mount(self) -> None:
        self.file = new_file()
        self.editor = Editor(self.file.content, name="editor")
        self.monitor = CodeViewer('\n'.join(self.editor.segments), name="viewer")

        self.directory = DirectoryTree(self.path, "directory")
        self.scroll_tree = ScrollView(self.directory)
        # Dock our widgets
        header = Header()
        header.title = "Noteterm"
        await self.view.dock(header, edge="top")
        await self.view.dock(Footer(), edge="bottom")

        # Note the directory is also in a scroll view
        await self.view.dock(self.scroll_tree,
                             edge="left", size=48, name="sidebar"
                             )

        await self.view.dock(self.editor, self.monitor, edge="left")

        await self.editor.focus()

    async def handle_file_click(self, message: FileClick) -> None:
        """A message sent by the directory tree when a file is clicked."""

        syntax: RenderableType
        try:

            self.file = load_file(message.path)
            self.app.sub_title = os.path.basename(message.path)
            self.editor = Editor(self.file.content, name="editor")
            self.monitor = CodeViewer('\n'.join(self.editor.segments), name="viewer")

        except Exception:
            # Possibly a binary file
            # For demonstration purposes we will show the traceback
            syntax = Traceback(theme="monokai", width=None, show_locals=True)


    async def action_save(self) -> None:
        self.file.content = '\n'.join(self.editor.segments)
        fname = self.file.fname.replace("/", "-")

        with open(os.path.join(self.path, fname), "w") as f:
            f.writelines(self.file.content)

        self.app.sub_title = f"{self.file.fname}"
        self.directory = DirectoryTree(self.path, "directory")
        await self.scroll_tree.update(self.directory)

    async def action_new(self):
        self.file = new_file()
        self.editor = Editor(self.file.content, name="editor")
        self.monitor = CodeViewer('\n'.join(self.editor.segments), name="viewer")

    async def on_key(self, event: events.Key) -> None:
        self.monitor.text = '\n'.join(self.editor.segments)


# Run our app class
NoteApp.run(title="Noteterm", log="textual.log")
