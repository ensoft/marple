from .Interface import perf


def perf_collect():
    """Uses perf module to collect scheduling data"""
    perf.collect_sched_all(10)

