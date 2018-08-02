# -------------------------------------------------------------
# datatypes.py - intermediate form of data to be converted
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

"""Data types for intermediate formats used in later data processing."""

from typing import NamedTuple


class SchedEvent(NamedTuple):
    """
    Represents a single scheduler event.
    :key time:
        The timesptamp of the event in Cpu ticks.
    :key type:
        The type of the event.
    :key track:
        The track that the event belongs to (e.g. cpu core, process, ...)
    :key datum:
        The data belonging to this event, (e.g. process id etc, cpu ... )

    """
    time: int
    type: str
    track: str
    datum: str

# class MemEvent(NamedTuple):
#     """Represents a single memory event."""
#     name: str
#     pid: int
#     cpu: int
#     time: str
#     duration: int
#     type: str
#     addr: str
#     func: str
#     lib: str


class StackEvent(NamedTuple):
    """Represents a single call stack"""
    # Could have more attributes if needed
    stack: tuple
