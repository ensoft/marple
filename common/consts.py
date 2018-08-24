# -------------------------------------------------------------
# consts.py - Various enums and other constants
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

"""
Module that defines various enums and constants used althroughout the interface
and display modules so that we avoid hard coded things and improve readability

"""

__all__ = (
    "DisplayOptions",
    "InterfaceTypes",
)

from enum import Enum


class DisplayOptions(Enum):
    # The values here should correspond to the ones from the config
    HEATMAP = "heatmap"
    STACKPLOT = "stackplot"
    FLAMEGRAPH = "flamegraph"
    TREEMAP = "treemap"
    G2 = "g2"


class InterfaceTypes(Enum):
    # The values here should correspond to the ones from the config
    SCHEDEVENTS = 'Scheduling Events'
    DISKLATENCY = 'Disk Latency/Time'
    MALLOCSTACKS = 'Malloc Stacks'
    MEMLEAK = 'Memory Leaks'
    MEMTIME = 'Memory/Time'
    CALLSTACK = 'Call Stacks'
    TCPTRACE = 'TCP Trace'
    MEMEVENTS = 'Memory Events'
    DISKBLOCK = 'Disk Block Requests'
    PERF_MALLOC = 'Perf Malloc Stacks'


class Datatypes(Enum):
    STACK = 'stack'
    EVENT = 'event'
    POINT = 'point'


# Display modes for the interfaces
display_dictionary = {
    Datatypes.EVENT: [DisplayOptions.G2],
    Datatypes.STACK: [DisplayOptions.HEATMAP, DisplayOptions.STACKPLOT],
    Datatypes.POINT: [DisplayOptions.TREEMAP,
                      DisplayOptions.FLAMEGRAPH],
}

interfaces_argnames = ["cpusched", "disklat", "ipc", "lib", "mallocstacks",
                       "memtime", "callstack", "memleak", "memevents",
                       "diskblockrq", "perf_malloc"]
