# -------------------------------------------------------------
# collecter.py - a superclass for all data-collecting interfaces
# August 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

from typing import NamedTuple
import datetime


class Collecter:
    """
    Base class for all collecter classes.

    Each such class should encapsulate a specific form of data collection.
    The collection should be for a certain length of time.
    Any options that may be passed can be transparently specified in the
    Options class as a NamedTuple.
    A set of default options should also ideally be specified.
    The data collection functionality should be carried out in the collect()
    method, and should ideally yield data one by one.

    """
    _DEFAULT_OPTIONS = None

    # Start and end times of data recording
    start_time: datetime.datetime
    end_time: datetime.datetime

    def __init__(self, time, options=_DEFAULT_OPTIONS):
        """
        Initialise the collecter.

        :param time:
            The length of time (in seconds) for which data should be collected.
        :param options:
            Any options that may be passed in to the collecter.

        """
        self.time = time
        self.options = options

    class Options(NamedTuple):
        """ Any options that may be passed in to the collecter."""
        pass

    def collect(self):
        """ Collect the data and return it. """
        pass

    def get_generator(self):
        """ Retrieves the datum generator """
        pass
