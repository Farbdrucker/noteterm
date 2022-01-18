import os
import string
import time
import uuid
from dataclasses import dataclass
from functools import partial

from pygments.lexers import get_lexer_by_name
from rich.console import RenderableType, Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.traceback import Traceback
from textual.app import App
from textual.widgets import Header, Footer, FileClick, ScrollView, DirectoryTree

# TODO
# 1. switching focus with tab
# 2. writing white space
# 3. toggle side bar
# 4. navigation with arrow keys
# 5. vim key bindings


ROOT = "./"
NAMING_SCHEME = "{time}_{head}{uuid}.md"


def readable_time(t_epoch) -> str:
    return time.strftime("%y-%m-%dT%H-%M", time.localtime(t_epoch))


example_md = """Start by entering a title
===
Happy hacking :)

"""


@dataclass
class File:
    timestamp: float
    content: str
    uuid: str

    __fname: str = None

    def set_fname(self, name: str) -> None:
        self.__fname = name

    @property
    def fname(self) -> str:
        if self.__fname is not None:
            return self.__fname
        else:
            # try to derive the file name from the header of the file
            rtime = readable_time(self.timestamp)

            header, divider = self.content.split("\n")[:2]
            head = (
                header.replace(" ", "-") + "_"
                if (divider.startswith("==") and header != "")
                else None
            )

            self.set_fname(NAMING_SCHEME.format(time=rtime, head=head, uuid=self.uuid))
        return self.fname


def new_file():
    return File(time.time(), content=example_md, uuid=uuid.uuid1())


def load_file(path: str) -> File:
    # try to decode timestamp
    # try to decode uuid

    fname = os.path.basename(path)
    with open(path, "r") as f:
        content = f.readlines()
    content = "".join(content)

    file = File(timestamp=0, content=content, uuid="-")
    file.set_fname(fname)
    return file


class Cursor:
    def __repr__(self):
        return "█"


cursor = Cursor()


class MyApp(App):
    """An example of a very simple Textual App"""

    async def on_load(self) -> None:
        """Sent before going in to application mode."""
        self.console = Console()
        self.file = new_file()

        # Bind our basic keys
        await self.bind("ctrl+b", "view.toggle('editor')", "Toggle editor")
        await self.bind("ctrl+v", "view.toggle('viewer')", "Toggle code viewer")
        await self.bind("ctrl+t", "view.toggle('tree)", "Toggle tree view")
        await self.bind("ctrl+q", "quit", "Quit")
        await self.bind("ctrl+s", "save", "Save")
        await self.bind("ctrl+n", "new", "New")

        # navigation
        for key in ("left", "up", "right", "down"):
            await self.bind(key, f"move_cursor_{key}", show=False)

        await self.bind("enter", "write_enter", show=False)
        setattr(self, f"action_write_enter", partial(self._write, "\n"))

        await self.bind(" ", "write_space")
        setattr(self, "action_write_space", partial(self._write, " "))

        await self.bind("ctrl+h", "delete_char", show=False)
        setattr(self, "action_delete_char", self._delete)
        #        await self.bind("h", "write_h",show=True)
        characters = (
            string.ascii_lowercase + string.ascii_uppercase + string.punctuation
        )

        for char in characters:
            await self.bind(char, f"write_{char}", show=False)
            setattr(self, f"action_write_{char}", partial(self._write, char))

        await self.bind(".", "write_fullstops", show=False)
        setattr(self, f"action_write_fullstops", partial(self._write, "."))

        await self.bind(",", "write_comma", show=False)
        setattr(self, f"action_write_comma", partial(self._write, ","))

    async def on_mount(self) -> None:
        """Call after terminal goes in to application mode"""

        # Create our widgets
        # In this a scroll view for the code and a directory tree
        self.editor = ScrollView(name="editor")
        # self.directory = DirectoryTree(self.path, "Code",)
        self.viewer = ScrollView(name="viewer")

        self.directory = DirectoryTree(ROOT, "directory")
        self.tree = ScrollView(self.directory, name="tree")

        # Dock our widgets
        await self.view.dock(Header(), edge="top")
        await self.view.dock(Footer(), edge="bottom")

        # Note the directory is also in a scroll view
        await self.view.dock(self.tree, self.editor, self.viewer, edge="left")

        await self._update()

    async def handle_file_click(self, message: FileClick) -> None:
        """A message sent by the directory tree when a file is clicked."""

        syntax: RenderableType
        try:
            # Construct a Syntax object for the path in the message
            self.file = load_file(message.path)

        except Exception:
            # Possibly a binary file
            # For demonstration purposes we will show the traceback
            syntax = Traceback(theme="monokai", width=None, show_locals=True)

        await self._update()

    async def _update(self) -> None:
        self.app.sub_title = self.file.fname

        content = self.file.content + str(cursor)
        self.syntax = Syntax(
            content,
            lexer=get_lexer_by_name("md"),
            line_numbers=True,
            word_wrap=True,
            indent_guides=True,
            theme="monokai",
        )
        await self.editor.update(self.syntax)

        await self.viewer.update(Markdown(self.file.content))

    def __dchar(self, num) -> None:
        self.file.content = self.file.content[:-num]

    def __add_cursor(self) -> None:
        if self.file.content[-1] != str(cursor):
            self.file.content += str(cursor)

    async def _write(self, text: str) -> None:
        self.file.content += text
        await self._update()

    async def _delete(self) -> None:
        self.__dchar(1)

        await self._update()

    async def action_save(self) -> None:
        fname = self.file.fname.replace("/", "-")

        with open(os.path.join(ROOT, fname), "w") as f:
            f.writelines(self.file.content)


#    async def action_write_h(self):
#        await self._write("h")


# Run our app class
MyApp.run(title="Code Viewer", log="textual.log")
