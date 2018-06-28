# Constants
blocking = False


def is_blocking():
    """
    Tell the caller if it should block waiting for the data collection to finish

    The calling module function, e.g. perf.collect can either return while data is still being collected
    or wait for the collection to finish. This function is called to tell it which of these it should do.

    :return:
        A boolean value that specifies whether to block
    """
    return blocking
