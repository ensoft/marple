# -------------------------------------------------------------
# sched_event.py - represents a scheduler event
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""Class for scheduler events"""

import collections


class SchedEvent(collections.namedtuple("_SchedEvent", "name, pid, cpu,"
                                                       "time, type")):
    """Represents a single scheduler event."""

