# -------------------------------------------------------------
# config.py - configuration of constants and defaults
# June - August 2018 - Franz Nowak, Andrei Diaconu
# -------------------------------------------------------------

"""
Implements a Parser class that interacts with the config file to get the default
values for various options

"""

__all__ = ["Parser"]

import os
import configparser


class Parser:
    DISPLAY_DIR = str(os.path.dirname(os.path.dirname(os.path.realpath(
                      __file__)))) + "/"

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.DISPLAY_DIR + "config.txt")

    def get_option_from_section(self, sec, opt, typ="string"):
        """
        Parses a section from the config file

        :param sec: the section we are reading from
        :param opt: the option we want to get
        :param typ: the type of the output, so we can parse it to the
                    appropriate type
        :return: a dictionary that has the as keys the fields of the provided
                 section
        """

        try:
            if typ == "string":
                value = self.config.get(sec, opt)
            elif typ == "int":
                value = self.config.getint(sec, opt)
            else:
                value = self.config.getboolean(sec, opt)
            return value
        except configparser.NoSectionError:
            print("Invalid section %s" % sec)
        except configparser.NoOptionError:
            print("Invalid option %s" % opt)
        except ValueError as err:
            print("Invalid type specified" + str(err))

    def get_default_blocking(self):
        """
        Return config value defining whether caller should block

        The calling module function, e.g. perf.collect can either
        return while data is still being collected
        or wait for the collection to finish.
        This function is called to tell it which of these it should do.

        :return:
            A boolean value that specifies whether to block
        """
        return self.get_option_from_section("General", "blocking", "boolean")

    def get_default_time(self):
        """
        Return the default time for which to collect data

        :return:
            The default time in seconds

        """
        return self.get_option_from_section("General", "time", "int")

    def get_default_frequency(self):
        """
        Return the default frequency

        :return:
            The default frequency in Hertz

        """
        return self.get_option_from_section("General", "frequency", "int")

    def get_system_wide(self):
        """
        Return the default coverage

        :return:
            The default coverage of the profiler as a string option

        """
        return self.get_option_from_section("General", "system_wide")
