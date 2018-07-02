# -------------------------------------------------------------
# perf.py - interacts with the perf command
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Interacts with the perf command

Calls perf to collect data for different purposes.

"""

__all__ = ["collect", "collect_sched_all", "map_sched", "get_sched_data"]

import subprocess
import src.common.config as config


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


def collect_sched_all(time):
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


def get_sched_data(filename):
    """
    Get the relevant scheduling data.

    This uses the previously by collect_sched collected data
    to output a list of relevant scheduler events in an ordered fashion.
    Note: this outputs all given events regardless of type.

    :param filename:
        Parameter for the user to decide how the
        file should be stored.

    :return:
        string of sched event lines of the form pid:cpu:time.

    """

    # Create file for recording output
    with open(filename, "w") as outfile:

        sub_process = subprocess.Popen(["perf", "sched", "script", "-F",
                                        "pid,cpu,time,event"], stdout=outfile)

        # Block if blocking is set by config module
        if config.is_blocking():
            sub_process.wait()
