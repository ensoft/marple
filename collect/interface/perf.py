# -------------------------------------------------------------
# perf.py - interacts with the perf tracing tool
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Interacts with the perf tracing tool.

Calls perf to collect data, format it, and has functions that create data
    object generators.

"""
__all__ = ["collect", "collect_sched", "get_stack_data", "get_sched_data"]

import logging
import os
import re
import subprocess

from common import (
    config,
    file,
    output
)
from ..converter.data_types import SchedEvent

# Constants for perf to stacks conversion
INCLUDE_TID = False
INCLUDE_PID = False

logger = logging.getLogger("collect.interface.perf")
logger.setLevel(logging.DEBUG)


def collect(time, frequency, cpufilter="-a"):
    """
    Collect system data using perf

    :param time:
        The time in seconds for which to collect the data.
    :param frequency:
        The frequency in Hz of taking samples.
    :param cpufilter:
        Optional parameter to filter for specific cpu core.

    """

    subprocess.call(["perf", "record", "-F", str(frequency), cpufilter, "-g",
                     "--", "sleep", str(time)])


def collect_sched(time):
    """
    Collect all CPU scheduling data using perf sched.

    This will get all the events in the scheduler.
    :param time:
        The time in seconds for which to collect the data.

    """
    subprocess.call(["perf", "sched", "record", "sleep", str(time)])


def get_stack_data():
    """
    Convert collected perf data to formatted stack data.

    :return:
        The temporary file that holds the output.

    """
    # Create temporary file for storing output
    filename = file.create_unique_temp_filename()

    sp = subprocess.Popen(["perf", "script"], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    with open(filename, "w") as outfile:
        outfile.write(sp.stdout.read().decode())
        logger.error(sp.stderr.read().decode())

    sp = StackParser(filename)
    return sp.stack_collapse()


def get_sched_data():
    """
    Get the relevant scheduling data.

    Creates and returns an iterator of scheduling event objects.

    :return:
        iterator of SchedEvent objects

    """
    # Create temporary file for recording output
    filename = file.create_unique_temp_filename()

    sp = subprocess.Popen(["perf", "sched", "script", "-F",
                           "comm,pid,cpu,time,event"],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

    with open(filename, "w") as outfile:
        outfile.write(sp.stdout.read().decode())
        logger.error(sp.stderr.read().decode())
        # Block if blocking is set by config module
        if config.is_blocking():
            sp.wait()

    return _sched_data_gen(filename)


def _sched_data_gen(filename):
    """
    Generator of SchedEvent objects from file

    Reads in the provided file, parses it and converts it into SchedEvent
        objects.

    :param filename:
        The name of the temporary file that contains structured perf sched
        output data generated in get_sched_data.

    :return
        an iterable of :class:`converter.data_types.SchedEvent` objects
            giving information about the process name, id, cpu core, time and
            the event type.

    """
    # Lazily return lines from the file as iterator
    with open(filename, "r") as infile:
        for event_data in infile:
            # e.g.   perf a  6997 [003] 363654.881950:       sched:sched_wakeup:
            match = re.match("\s*"
                             "(?P<name>\S+(\s+\S+)*)\s+"
                             "(?P<pid>\d+)\s+"
                             "\[(?P<cpu>\d+)\]\s+"
                             "(?P<time>\d+.\d+):\s+"
                             "(?P<event>\S+)", event_data)

            # If it did not match, log it but continue
            if match is None:
                logger.debug("Failed to parse event data: {} Expected "
                             "format: name pid cpu time event".format(
                    event_data))
                continue

            event = SchedEvent(name=match.group("name"),
                               pid=int(match.group("pid")),
                               cpu=int(match.group("cpu")),
                               time=match.group("time"),
                               type=match.group("event"))

            yield event

    # Delete file after we finished using it.
    os.remove(filename)


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

    _stackline = r"\s*(?P<pc>\w+)\s*(?P<rawfunc>.+)\((?P<mod>\S*)\)"
    # Matches the other lines of a stack, i.e. the ones above the base.
    # e.g ffffffffabe0c31d intel_pmu_enable_ ([kernel.kallsyms])

    _symbol_offset = r"\+0x[\da-f]+$"
    # Matches symbol offset
    # eg in: 7fffb84c9afc cpu_startup_entry+0x800047c022ec ([kernel.kallsyms])

    # --------------------------------------------------------

    # The cached stack data
    stack = []
    # The process name
    pname = None
    # Variables to handle filtering for only one event
    event_filter = ""
    event_defaulted = False
    event_warning = False

    def __init__(self, filename):
        """ Initialises the Parser.

        :param filename:
            A text file or similar input containing lines of stack data
            output from perf.

        """

        self.filename = filename

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
        #   that past ones have been filtered
        if self.pname is None:
            return

        # Finish making the stack and yield it
        self.stack.insert(0, self.pname)
        yield tuple(self.stack)

        # Reset the cache
        self.stack = []
        self.pname = None

    def _parse_baseline(self, line):
        """Matches a stack baseline and extracts its info."""

        m = re.match(self._baseline, line)
        # eg. "java 25607 4794564.109216: cycles:"

        (comm, pid) = m.group("comm"), m.group("pid")

        try:
            tid = m.group("tid")

        except IndexError:
            # No tid found (only third group is optional)
            tid = pid
            pid = "?"

        if re.search(self._eventtype, line):
            # Matches the event type of the stack, found at the
            #   end of the baseline
            # e.g. cycles:ppp:

            m = re.search(self._eventtype, line)
            # By default only show events of the first encountered
            #   event type. Merging together different types,
            #   such as instructions and cycles, produces
            #   misleading results.
            event = m.group(1)

            if self.event_filter == "":
                self.event_defaulted = True

            elif event != self.event_filter:
                if self.event_defaulted and not self.event_warning:
                    # only print this warning if necessary:
                    # when we defaulted and there were
                    # multiple event types.
                    logger.error("Filtering for events of type {}"
                                 .format(self.event_filter))
                    self.event_warning = True
                return

        if INCLUDE_TID:
            self.pname = "{}-{}/{}".format(comm, pid, tid)
        elif INCLUDE_PID:
            self.pname = "{}-{}".format(comm, pid)
        else:
            self.pname = comm
        # replace space with underscore
        self.pname = re.sub("\s", "_", self.pname)

    def _parse_stackline(self, line):
        """Matches a stack line that is not a baseline and extracts its info."""

        m = re.match(self._stackline, line)
        # e.g ffffffffabe0c31d intel_pmu_enable_ ([kernel.kallsyms])

        # Ignore filtered samples
        if self.pname is None:
            return

        pc, rawfunc, mod = m.group("pc"), m.group("rawfunc").rstrip(), \
                           m.group("mod")

        # Linux 4.8 includes symbol offsets in perf script output,
        # eg 7fffb84c9afc cpu_startup_entry+0x800047c022ec
        #   ([kernel.kallsyms])

        # strip these off:
        rawfunc = re.sub(self._symbol_offset, "", rawfunc)

        # Original perl script adds inline here if required by user

        # Skip process names
        if re.match("\(", rawfunc):
            return

        # Not sure what inlining is for...
        inline = ""
        for func in re.split("->", rawfunc):
            if func == "[unknown]":
                # use module name instead, if known
                if mod != "[unknown]":
                    func = mod
                    func = re.sub(".*/", "", func)

            # TODO: Tidy generic stuff

            if len(inline) > 0:
                # Mark as inlined
                func += "_[i]"

            inline += func

        self.stack.insert(0, inline)

    def stack_collapse(self):
        """
        Goes through input line by line to fold the stacks.

        Calls the appropriate function to parse each line.
        Returns a generator to get single stacks lazily.

        :return:
            An iterable of tuples that contain information about stacks.

        """

        logger.info("Starting to convert perf output to stacks")
        with(open(self.filename, "r")) as input_:

            for line in input_:

                # If end of stack, save cached data.
                if self._line_is_empty(line):
                    # Matches empty line
                    self._make_stack()

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
                    logger.error("Unrecognized line: {}".format(line))

        logger.info("Conversion to stacks successful")
