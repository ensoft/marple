# -------------------------------------------------------------
# generic_controller.py - a unified interface for all the controllers
# August 2018 - Andrei Diaconu, Hrutvik Kanabar
# -------------------------------------------------------------

import logging
from common import util

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


class GenericController:
    """
    A blind generic controller

    """
    def __init__(self, collecter, writer, filename):
        """
        Initialises the Controller
        :param collecter: class that resides in one of the interfaces,
                          which must inherit the generic interface; it collects
                          data
        :param writer: one of the writing modules, which must inherit the
                       generic writer interface; it writes the data in some
                       format
        :param filename: the filename we use to write the data

        """
        self.collecter = collecter
        self.writer = writer
        self.filename = filename

    @util.log(logger)
    def run(self):
        # We collect the data first
        data = self.collecter.collect()

        # We then write it
        self.writer.write(data, self.filename)
