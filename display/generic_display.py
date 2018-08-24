# -------------------------------------------------------------
# generic_display.py - Implements an interface for all the display classes
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

__all__ = "GenericDisplay"

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

    class DataOptions(NamedTuple):
        """
        Any options that the data might have. Could be units in which it is
        measured or any data related properties

        """
        pass

    def __init__(self, data_options, display_options):
        self.display_options = display_options
        self.data_options = data_options

    def show(self):
        pass
