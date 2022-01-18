import os
import time
import uuid
from dataclasses import dataclass

from utils.time import readable_time

example_md = """Start by entering a title
===
Happy hacking :)

"""

NAMING_SCHEME = "{time}_{head}{uuid}.md"

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