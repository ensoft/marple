# -------------------------------------------------------------
# generic_display.py - Implements an interface for all the display classes
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

__all__ = "GenericDisplay"


class GenericDisplay:
    """
    An interface for display classes

    """
    def make(self):
        pass

    def show(self):
        pass