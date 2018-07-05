# -------------------------------------------------------------
# perf.py - interacts with the perf command
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Interacts with the perf command

Calls perf to collect data for different purposes.

"""

import os
import subprocess
import common.config as config
import common.file as file
from collect.converter.sched_event import SchedEvent

__all__ = ["collect", "collect_sched", "map_sched", "get_sched_data"]


def collect(time, frequency):
    """
    Collect system data using perf

    :param time:
        The time in seconds for which to collect the data.

    :param frequency:
        The frequency in Hz of taking samples

    """

    subprocess.call(["perf", "record", "-F", str(frequency), "-a", "-g", "--",
                     "sleep", str(time)])


def collect_sched(time):
    """
    Collect all CPU scheduling data using perf sched.

    This will get all the events in the scheduler.
    :param time:
        The time in seconds for which to collect the data.

    """
    subprocess.call(["perf", "sched", "record", "sleep", str(time)])


def map_sched():
    """
    Display the collected scheduling data as a map.

    Each columns represents a CPU core, each entry is
    a process whose name can be found in the legend
    on the right.

    """
    subprocess.call(["perf", "sched", "map"])


def get_sched_data():
    """
    Get the relevant scheduling data.

    Creates and returns an iterator of scheduling event objects.

    :return:
        iterator of SchedEvent objects

    """
    # Create temporary file for recording output
    filename = file.create_name()

    with open(filename, "w") as outfile:

        sub_process = subprocess.Popen(["perf", "sched", "script", "-F",
                                        "comm,pid,cpu,time,event"], stdout=outfile)

        # Block if blocking is set by config module
        if config.is_blocking():
            sub_process.wait()

    iterator = _data_gen(filename)

    return iterator


def _data_gen(filename):
    """
    Generator of SchedEvent objects from file

    Reads in the provided file, parses it and converts it into SchedEvent
    objects.

    :param filename:
        Parameter for the user to decide how the
        file should be stored.

    :return
        SchedEvent object Iterator

    """
    # lazily return lines from the file as iterator
    with open(filename, "r") as infile:
        while True:
            event_data = infile.readline()
            if not event_data:
                break
            (name, pid, cpu, time, event) = event_data.split()
            event = SchedEvent(name=name, pid=pid, cpu=cpu, time=time, type=event)
            yield event

    os.remove(filename)
