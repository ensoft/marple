# -------------------------------------------------------------
# config.py - configuration of constants and defaults
# June - September 2018 - Franz Nowak, Andrei Diaconu, Hrutvik Kanabar
# -------------------------------------------------------------

"""
Interacts with the MARPLE config file.

The config file is located in ~/.marpleconfig.
If no config file exists, the default one will be copied to the config location.
The default config file can be found in the marple package (with __main__.py)

"""

__all__ = (
    'config',
    'get_option_from_section',
    'get_section',
)

import os
import configparser
import logging
from shutil import copyfile

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


CONFIG_FILE = os.path.expanduser('~/.marpleconfig')
DEFAULTS_FILE = os.path.dirname(os.path.dirname(__file__)) + "/config.txt"

if not os.path.exists(CONFIG_FILE):
    copyfile(DEFAULTS_FILE, CONFIG_FILE)

config = configparser.ConfigParser()
config.read(CONFIG_FILE)


def get_option_from_section(sec, opt, typ="string"):
    """
    Parses a section from the config file

    :param sec:
        the section we are reading from
    :param opt:
        the option we want to get
    :param typ:
        the type of the output, so we can parse it to the appropriate type
    :return:
        a dictionary that has the as keys the fields of the provided section

    """

    if typ == "string":
        value = config.get(sec, opt)
    elif typ == "int":
        value = config.getint(sec, opt)
    elif typ == "bool":
        value = config.getboolean(sec, opt)
    elif typ == "float":
        value = config.getfloat(sec, opt)
    else:
        raise ValueError("Invalid type specified to read from config: {}."
                         .format(typ))

    return value


def get_section(sec):
    """
    Retrieves a section from the config

    :param sec:
        section we want to retrieve
    :return:
        the section as a dict

    """
    try:
        return config[sec]
    except ValueError as ve:
        raise ValueError("The section {} is not in the config".format(sec)) \
            from ve


def get_default_time():
    """
    Return the default time for which to collect data

    :return:
        The default time in seconds

    """
    return get_option_from_section("General", "time", "int")
