# -------------------------------------------------------------
# interface.py - a superclass for all data-collecting interfaces
# August 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

from typing import NamedTuple


class Collecter:

    _DEFAULT_OPTIONS = None

    def __init__(self, time, options=_DEFAULT_OPTIONS):
        self.time = time
        self.options = options

    class Options(NamedTuple):
        pass

    def collect(self):
        pass
