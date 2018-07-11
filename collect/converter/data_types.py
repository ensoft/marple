# -------------------------------------------------------------
# data_types.py - intermediate form of data to be converted
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""Data types for intermediate formats used in later data processing."""
import re
from typing import NamedTuple

from common import output


class SchedEvent(NamedTuple):
    """Represents a single scheduler event."""
    name: str
    pid: int
    cpu: str
    time: str
    type: str

    def __init__(self):
        # strip off brackets (for perf output)
        if re.match("\[\d+\]", self.cpu) is not None:
            re.sub("\[", "", self.cpu)
            re.sub("\]", "", self.cpu)

        # convert to int
        try:
            self.cpu = int(self.cpu)
        except ValueError as verr:
            output.error("Unexpected formatting error. "
                         "Please refer to log for details.",
                         "Wrong format detected, cpu in sched event "
                         "is not a number")
