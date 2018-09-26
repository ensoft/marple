# -------------------------------------------------------------
# generic_display.py - Implements an interface for all the display classes
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

__all__ = ("GenericDisplay",)

from typing import NamedTuple


class GenericDisplay:
    """
    An interface for display classes to implement

    """

    class DisplayOptions(NamedTuple):
        """
        Any options that the display  might have. To be overriden in its
        implementation.

        """
        pass

    def __init__(self, data, *args):
        """
        Initialises the display module

        :param data: a derivative of a `data_io.Data` object
        :param args: extra args
        """
        self.data = data
        self.data_options = data.data_options

    def show(self):
        """
        Method that actually displays the data

        """
        pass
