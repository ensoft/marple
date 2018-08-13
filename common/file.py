# -------------------------------------------------------------
# file.py - generates unique file filenames
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Handles the naming of files.

Provides functions to either create a filename from a given name or to
generate a unique generic filename including the appropriate directory name.
Can also export them to disk.

"""

__all__ = (
    'DisplayFileName',
    'DataFileName',
    'TempFileName'
)

import logging
import os
from datetime import datetime

from common import paths

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class _FileName:

    def __init__(self, option, extension, given_name=None, path=paths.OUT_DIR):
        self.datetime = datetime.now()
        self.option = option
        self.extension = extension
        if given_name == "":
            raise FileNotFoundError("Cannot have empty file name.")
        elif given_name is None:
            self.given_name = None
            self.path = path
        else:
            dir_name = os.path.dirname(given_name)
            if os.path.isdir(dir_name):
                self.path = dir_name + "/"
                self.given_name = os.path.basename(given_name)
            else:
                self.path = path
                self.given_name = given_name

    def __str__(self):
        if self.given_name is None:
            date = self.datetime.strftime("%Y-%m-%d_%H:%M:%S.%f")
            result = self.path + date
            if self.option is None:
                result += "." + self.extension
            else:
                result += "_" + self.option + "." + self.extension
        else:
            result = self.path + self.given_name
        return result

    def __repr__(self):
        return self.__str__()


class DisplayFileName(_FileName):

    def __init__(self, option=None,
                 extension="marple.display", given_name=None):
        super().__init__(option, extension, given_name)

    def set_options(self, option, extension):
        self.option = option
        self.extension = extension


class DataFileName(_FileName):

    def __init__(self, given_name=None):
        super().__init__(None, "marple", given_name)

    def export_filename(self):
        with open(paths.VAR_DIR + "filename", "w") as file:
            file.write(str(self))

    @classmethod
    def import_filename(cls):
        try:
            with open(paths.VAR_DIR + "filename", "r") as saved_filename:
                return saved_filename.readline().strip()
        except FileNotFoundError:
            logger.error("Unable to find filename helper file in %s",
                         str(paths.VAR_DIR))
            raise


class TempFileName(_FileName):
    def __init__(self):
        super().__init__(None, "tmp", path=paths.TMP_DIR)
