from rich.console import RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from textual.widget import Widget

# Todo make CodeViewer as  ScrollView

class CodeViewer(Widget):
    def __init__(self, text: str, *args, **kwargs):
        super(CodeViewer, self).__init__(*args, **kwargs)
        self.text = text

    def on_mount(self):
        self.set_interval(1, self.refresh)

    def render(self) -> RenderableType:

        return Panel(Markdown(self.text), title="Markdown Preview")