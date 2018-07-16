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

    return _stack_collapse(filename)


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


def _stack_collapse(filename):
    """
    Goes through input line by line to fold the stacks.

    This function is a Python adaptation of Brendan Gregg's Perl script
    stackcollapse-perf.pl from his flamegraph repository.
    It differs in that it has fewer options and returns a generator to get
    single stacks lazily and without counting them.
    This is in order to integrate it with the marple program structure.

    :param filename:
        A text file or similar input containing lines of stack data
        output from perf.

    :return:
        A generator of lists that contain information about a single stack.
    """
    stack = []
    pid = None
    comm = None
    pname = None
    event_filter = ""
    event_defaulted = False
    event_warning = False

    logger.info("Starting to convert perf output to stacks")
    with(open(filename, "r")) as input_:
        for line in input_:
            # If end of stack, save cached data.
            if re.match("^$", line) is not None:
                # ignore filtered samples
                if pname is None:
                    continue
                stack.insert(0, pname)
                if stack:
                    yield tuple(stack)
                stack = []
                pname = None
                continue

            #
            # event record start
            #
            if re.match("(\S.+?)\s+(\d+)/*(\d+)*\s+", line) is not None:
                # Matches "perf script" output, first line of a stack (baseline)
                # eg, "java 25607 4794564.109216: cycles:"
                # eg, "java 12688 [002] 6544038.708352: cpu-clock:"
                # eg, "V8 WorkerThread 25607 4794564.109216: cycles:"
                # eg, "java 24636/25607 [000] 4794564.109216: cycles:"
                # eg, "java 12688/12764 6544038.708352: cpu-clock:"
                # eg, "V8 WorkerThread 24636/25607 [000] 94564.109216: cycles:"
                # other combinations possible
                m = re.match("(\S.+?)\s+(\d+)/*(\d+)*\s+", line)
                try:
                    (comm, pid, tid) = m.group(1), m.group(2), m.group(3)
                except IndexError:
                    # No tid found
                    tid = pid
                    pid = "?"
                m = re.search("(\S+):\s*$", line)
                if m is not None:
                    # By default only show events of the first encountered
                    # event type. Merging together different types, such as
                    # instructions and cycles, produces misleading results.
                    event = m.group(1)
                    if event_filter == "":
                        # By default only show events of the first
                        # encountered event type. Merging together different
                        # types, such as instructions and cycles, produces
                        # misleading results.
                        event_filter = event
                        event_defaulted = True
                    elif event != event_filter:
                        if event_defaulted and not event_warning:
                            # only print this warning if necessary:
                            # when we defaulted and there was
                            # multiple event types.
                            logger.error("Filtering for events of type {}"
                                         .format(event_filter))
                            event_warning = True
                        continue

                (m_pid, m_tid) = pid, tid

                if INCLUDE_TID:
                    pname = "{}-{}/{}".format(comm, m_pid, m_tid)
                elif INCLUDE_PID:
                    pname = "{}-{}".format(comm, m_pid)
                else:
                    pname = comm

                # original perl script has transliteration here:
                # $pname =~ tr/ /_/;

            #
            # stack line
            #
            elif re.match("\s*(\w+)\s*(.+)\((\S*)\)", line) is not None:
                # Matches the other lines of a stack,
                # i.e. the ones above the base.
                # e.g ffffffffabe0c31d _intel_pmu_enable_ ([kernel.kallsyms])
                m = re.match("\s*(\w+)\s*(.+)\((\S*)\)", line)

                # ignore filtered samples
                if pname is None:
                    continue

                pc, rawfunc, mod = m.group(1), m.group(2).rstrip(), m.group(3)

                # Linux 4.8 included symbol offsets in perf script output by
                # default, eg:
                # 7fffb84c9afc cpu_startup_entry+0x800047c022ec
                # ([kernel.kallsyms])
                # strip these off:
                rawfunc = re.sub("\+0x[\da-f]+$", "", rawfunc)

                # Original perl script adds inline here if required by user

                # skip process names
                if re.match("\(", rawfunc):
                    continue

                inline = ""
                for func in re.split("->", rawfunc):
                    if func == "[unknown]":
                        # use module name instead, if known
                        if mod != "[unknown]":
                            func = mod
                            func = re.sub(".*/", "", func)

                        # Original perl script has option to include address.
                    # Original perl script has some optional tidying up here for
                    # Java and other generic stuff

                    if len(inline) > 0:
                        # Mark as inlined
                        func += "_[i]"

                    inline += func

                stack.insert(0, inline)

            else:
                logger.error("Unrecognized line: {}".format(line))
    logger.info("Conversion to stacks successful")
