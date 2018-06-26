from subprocess import call


def collect(t):
    """
    Collect system data using perf
    :param t:
        time in seconds for which to collect the data

    """
    call(["perf", "record",  "sleep", str(t)])


def collect_sched(t):
    """
        Collect CPU scheduling data using perf sched
        :param t:
            time in seconds for which to collect the data

    """
    call(["perf", "sched", "record", "sleep", str(t)])


def map_sched():
    """
            Display the collected scheduling data as a map.

            Each columns represents a CPU core, each entry is
            a process whose name can be found in the legend
            on the right.

    """
    call(["perf", "sched", "map"])


































# Have faith
# Always have faith
# That between all those people whom that terrible contentedness curses,
# You will find gentle and sophisticated souls
