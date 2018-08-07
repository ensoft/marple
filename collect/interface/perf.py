# -------------------------------------------------------------
# perf.py - interacts with the perf tracing tool
# June-July 2018 - Franz Nowak, Hrutvik Kanabar, Andrei Diaconu
# -------------------------------------------------------------

"""
Interacts with the perf tracing tool.

Calls perf to collect data, format it, and has functions that create data
    object generators.

"""

__all__ = (
    'MemoryEvents',
    'MemoryMalloc',
    'StackTrace',
    'SchedulingEvents',
    'DiskBlockRequests'
)

import logging
import re
import subprocess
from io import StringIO
from common import util
from typing import NamedTuple

from common import (
    datatypes
)
from collect.interface.collecter import Collecter

# Constants for perf to stacks conversion
INCLUDE_TID = False
INCLUDE_PID = False

logger = logging.getLogger(__name__)
logger.debug('Entered module: {}'.format(__name__))

# @@@ TODO add blocking based on config file


class MemoryEvents(Collecter):

    class Options(NamedTuple):
        pass

    _DEFAULT_OPTIONS = None

    @util.check_kernel_version("2.6")
    @util.Override(Collecter)
    def __init__(self, time, options=_DEFAULT_OPTIONS):
        super().__init__(time, options)

    @util.log(logger)
    @util.Override(Collecter)
    def collect(self):
        sub_process = subprocess.Popen(
            ["perf", "record", "-ag", "-e", "'{mem-loads,mem-stores}'",
             "sleep", str(self.time)], stderr=subprocess.PIPE)
        _, err = sub_process.communicate()
        logger.debug(err.decode())

        sub_process = subprocess.Popen(["perf", "script"],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        out, err = sub_process.communicate()

        logger.error(err.decode())

        stack_parser = StackParser(out.decode())
        return stack_parser.stack_collapse()


class MemoryMalloc(Collecter):

    class Options(NamedTuple):
        pass

    _DEFAULT_OPTIONS = None

    @util.check_kernel_version("2.6")
    @util.Override(Collecter)
    def __init__(self, time, options=_DEFAULT_OPTIONS):
        super().__init__(time, options)

    @util.log(logger)
    @util.Override(Collecter)
    def collect(self):
        # Delete old probes and create a new one tracking allocation size
        # @@@ TODO THIS IS ARCHITECTURE SPECIFIC CURRENTLY
        sub_process = subprocess.Popen(
            ["perf", "probe", "-q", "--del", "*malloc*"],
            stderr=subprocess.PIPE)
        _, err = sub_process.communicate()
        logger.debug(err.decode())

        sub_process = subprocess.Popen(
            ["perf", "probe", "-qx", "/lib*/*/libc.so.*",
             "malloc:1 size=%di"], stderr=subprocess.PIPE)
        _, err = sub_process.communicate()
        logger.debug(err.decode())

        # Record perf data
        sub_process = subprocess.Popen(
            ["perf", "record", "-ag", "-e", "probe_libc:malloc:",
             "sleep", str(self.time)], stderr=subprocess.PIPE)
        _, err = sub_process.communicate()
        logger.debug(err.decode())

        sub_process = subprocess.Popen(["perf", "script"],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        out, err = sub_process.communicate()

        logger.error(err.decode())

        stack_parser = StackParser(out.decode())
        return stack_parser.stack_collapse()


class StackTrace(Collecter):

    class Options(NamedTuple):
        frequency: int
        cpufilter: str

    _DEFAULT_OPTIONS = Options(frequency=99, cpufilter="-a")

    @util.check_kernel_version("2.6")
    def __init__(self, time, options=_DEFAULT_OPTIONS):
        super().__init__(time, options)

    @util.log(logger)
    @util.Override(Collecter)
    def collect(self):
        sub_process = subprocess.Popen(["perf", "record", "-F",
                                        str(self.options.frequency),
                                        self.options.cpufilter,
                                        "-g", "--", "sleep",
                                        str(self.time)],
                                       stderr=subprocess.PIPE)
        _, err = sub_process.communicate()
        logger.debug(err.decode())

        sub_process = subprocess.Popen(["perf", "script"],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

        out, err = sub_process.communicate()

        logger.error(err.decode())

        stack_parser = StackParser(out.decode())
        return stack_parser.stack_collapse()


class SchedulingEvents(Collecter):

    class Options(NamedTuple):
        pass

    _DEFAULT_OPTIONS = None

    @util.check_kernel_version("2.6")
    def __init__(self, time, options=_DEFAULT_OPTIONS):
        super().__init__(time, options)

    @util.log(logger)
    @util.Override(Collecter)
    def collect(self):
        sub_process = subprocess.Popen(["perf", "sched", "record", "sleep",
                                        str(self.time)], stderr=subprocess.PIPE)
        _, err = sub_process.communicate()
        logger.debug(err.decode())

        sub_process = subprocess.Popen(["perf", "sched", "script", "-F",
                                        "comm,pid,cpu,time,event"],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        out, err = sub_process.communicate()
        logger.error(err.decode())

        for event_data in StringIO(out.decode()):
            # e.g.   perf a  6997 [003] 363654.881950:       sched:sched_wakeup:

            event_data = event_data.strip()

            match = re.match(r"\s*"
                             r"(?P<name>\S+(\s+\S+)*)\s+"
                             r"(?P<pid>\d+)\s+"
                             r"\[(?P<cpu>\d+)\]\s+"
                             r"(?P<time>\d+.\d+):\s+"
                             r"(?P<event>\S+)", event_data)

            # If it did not match, log it but continue
            if match is None:
                logger.error("Failed to parse event data: %s Expected "
                             "format: name pid cpu time event",
                             event_data)
                continue

            # Convert time format to us. Perf output: [seconds].[us]
            time_str = match.group("time").split(".")
            time_int = int(time_str[0]) * 1000000 + int(time_str[1])

            # Create datum from name and pid:
            datum = "{} (pid: {})".format(match.group("name"),
                                          match.group("pid"))

            # Create track name from cpu:
            track = "cpu " + str(int(match.group("cpu")))

            event = datatypes.SchedEvent(datum=datum,
                                         track=track,
                                         time=time_int,
                                         type=match.group("event"))

            yield event


class DiskBlockRequests(Collecter):

    class Options(NamedTuple):
        pass

    _DEFAULT_OPTIONS = None

    @util.check_kernel_version("2.6")
    def __init__(self, time, options=_DEFAULT_OPTIONS):
        super().__init__(time, options)

    @util.log(logger)
    @util.Override(Collecter)
    def collect(self):
        sub_process = subprocess.Popen(
            ["perf", "record", "-ag", "-e", "block:block_rq_insert",
             "sleep", str(self.time)], stderr=subprocess.PIPE)
        _, err = sub_process.communicate()
        logger.debug(err.decode())

        sub_process = subprocess.Popen(["perf", "script"],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        out, err = sub_process.communicate()
        logger.error(err.decode())

        stack_parser = StackParser(out.decode())
        return stack_parser.stack_collapse()


class StackParser:
    """
    Goes through input line by line to fold the stacks.

    Takes stacks that were captured by perf and converts them to stack objects.

    """
    # ---------------------------------------------------------
    # Regular expressions to match lines of the perf output:

    _emptyline = r"$^"
    # Matches an empty line

    _baseline = r"(?P<comm>\S.+?)\s+(?P<pid>\d+)/*(?P<tid>\d+)*\s+"
    # Matches "perf script" output, first line of a stack (baseline)
    # eg. "java 25607 4794564.109216: cycles:"
    # or  "V8 WorkerThread 24636/25607 [002] 6544038.708352: cpu-clock:"

    _eventtype = r"(?P<event>\S+):\s*$"
    # Matches the event type of the stack, found at the end of the baseline
    #   e.g. cycles:ppp:

    _stackline = r"\s*\w+\s*(?P<rawfunc>.+)\((?P<mod>\S*)\)"
    # Matches the other lines of a stack, i.e. the ones above the base.
    # e.g ffffffffabe0c31d intel_pmu_enable_ ([kernel.kallsyms])

    _symbol_offset = r"\+0x[\da-f]+$"
    # Matches symbol offset
    # eg in: 7fffb84c9afc cpu_startup_entry+0x800047c022ec ([kernel.kallsyms])

    # --------------------------------------------------------

    def __init__(self, data_in, event_filter=""):
        """ Initialises the Parser.

        :param data_in:
            Input from perf.
        :param event_filter:
            An optional string argument for an event type to be filtered for.
            Empty defaults to the first event type that is encountered.

        """
        self.data = data_in
        self.event_filter = event_filter

        # _stack: A list containing the cached stack data
        self._stack = []
        # _pname: A string, the extracted current process name
        self._pname = None
        # event_defaulted: A Boolean flag to show the event_filter defaulted.
        self._event_defaulted = False
        # event_warning: A Boolean flag that stores whether we've warned before.
        self._event_warning = False

    def _line_is_empty(self, line):
        """Checks whether line is an empty line."""

        return re.match(self._emptyline, line) is not None

    def _line_is_baseline(self, line):
        """Checks whether a line is a stack baseline."""

        return re.match(self._baseline, line) is not None

    def _line_is_stackline(self, line):
        """Checks whether a line is a stack line that is not a baseline."""

        return re.match(self._stackline, line) is not None

    def _make_stack(self):
        """Creates a stack tuple from cached data and yields it."""

        # if there is no pname, we have not processed one yet, which means
        #   that past ones have been filtered (_pname used as flag)
        if self._pname is None:
            return None

        # Finish making the stack and yield it
        self._stack.insert(0, self._pname)

        stack_folded = tuple(self._stack)

        # Reset the cache
        self._stack = []
        self._pname = None

        return stack_folded

    def _parse_baseline(self, line):
        """Matches a stack baseline and extracts its info."""

        match = re.match(self._baseline, line)
        # eg. "java 25607 4794564.109216: cycles:"

        (comm, pid) = match.group("comm"), match.group("pid")

        try:
            tid = match.group("tid")

        except IndexError:
            # No tid found
            tid = pid
            pid = "?"

        if re.search(self._eventtype, line):
            # Matches the event type of the stack, found at the end of the
            #   baseline.
            # e.g. cycles:ppp:

            match = re.search(self._eventtype, line)
            # By default only show events of the first encountered event
            #   type. Merging together different types, such as instructions
            #   and cycles, produces misleading results.
            event = match.group(1)

            # If the event_filter was not specified by the caller, default.
            if self.event_filter == "":
                self.event_filter = event
                self._event_defaulted = True

            elif event != self.event_filter:
                if self._event_defaulted and not self._event_warning:
                    # only print this warning if necessary: when we defaulted
                    #  and there were multiple event types.
                    logger.error("Filtering for events of type %s",
                                 self.event_filter)
                    self._event_warning = True
                return

        if INCLUDE_TID:
            self._pname = "{}-{}/{}".format(comm, pid, tid)
        elif INCLUDE_PID:
            self._pname = "{}-{}".format(comm, pid)
        else:
            self._pname = comm
        # replace space with underscore in pname
        self._pname = re.sub(r"\s", "_", self._pname)

    def _parse_stackline(self, line):
        """Matches a stack line that is not a baseline and extracts its info."""

        match = re.match(self._stackline, line)
        # e.g ffffffffabe0c31d intel_pmu_enable_ ([kernel.kallsyms])

        # Ignore filtered samples, _pname used as flag
        if self._pname is None:
            return

        rawfunc, mod = match.group("rawfunc").rstrip(), match.group("mod")

        # Linux 4.8 includes symbol offsets in perf script output,
        # eg 7fffb84c9afc cpu_startup_entry+0x800047c022ec([kernel.kallsyms])

        # strip these off:
        rawfunc = re.sub(self._symbol_offset, "", rawfunc)

        # Can add inline here if selected

        # Skip process names
        if re.match(r"\(", rawfunc):
            return

        # Not sure what inline stands for...
        inline = ""
        for func in re.split("->", rawfunc):
            if func == "[unknown]":
                # use module name instead, if known
                if mod != "[unknown]":
                    func = mod
                    func = re.sub(".*/", "", func)

            if inline != "":
                # Mark as inlined
                func += "_[i]"

            inline += func

        self._stack.insert(0, inline)

    @util.log(logger)
    def stack_collapse(self):
        """
        Goes through input line by line to fold the stacks.

        Calls the appropriate function to parse each line.
        Returns a generator to get single stacks lazily.

        :return:
            An iterable of tuples that contain information about stacks.

        """

        for line in StringIO(self.data):
            # If end of stack, save cached data.
            if self._line_is_empty(line):
                # Matches empty line
                stack_folded = self._make_stack()
                if stack_folded:
                    yield datatypes.StackData(weight=1, stack=stack_folded)
                    # @@@ TODO: generalise to allow different weights
            # event record start
            elif self._line_is_baseline(line):
                # Matches "perf script" output, first line of a stack
                self._parse_baseline(line)

            # stack line
            elif self._line_is_stackline(line):
                # Matches the other lines of a stack above the baseline
                self._parse_stackline(line)

            # if nothing matches, log an error
            else:
                logger.error("Unrecognized line: %s", line)
