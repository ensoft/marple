from src.interface import perf


def collect(t=10):
    """
    Uses perf module to collect scheduling data

    :param t:
        time in seconds for the data to be collected

    """
    perf.collect_sched_all(t)
