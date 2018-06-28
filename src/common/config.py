# Constants

blocking = False
time = 10
frequency = 99
# The default frequency is 99 rather than 100 to avoid
# recording in lockstep with some periodic activity.


def is_blocking():
    """
    Return config value defining whether caller should block waiting for the data collection to finish

    The calling module function, e.g. perf.collect can either return while data is still being collected
    or wait for the collection to finish. This function is called to tell it which of these it should do.

    :return:
        A boolean value that specifies whether to block
    """
    return blocking


def get_default_time():
    """
            Return the default time for which to collect data

            :return:
                The default time in seconds

            """
    return time


def get_default_frequency():
    """
        Return the default frequency

        :return:
            The default frequency in Hertz

        """
    return frequency
