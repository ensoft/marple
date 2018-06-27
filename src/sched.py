from .Interface import perf


def collect(t = 10, f = 100):
    """
    Uses perf module to collect scheduling data

    :param t:
        time in seconds for the data to be collected

    :param f:
        frequency of taking samples in Hz

    """
    perf.collect_sched_all(t, f)

