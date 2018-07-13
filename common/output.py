# -------------------------------------------------------------
# output.py - displays output to the user and logs it.
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Displays output to the user and logs it.

Provides functions for normal print output and errors.
"""
__all__ = ["print_", "error_"]

import logging

logger = logging.getLogger("common.output")
logger.setLevel(logging.DEBUG)


def print_(text):
    """
    Displays normal output to the user and logs it.

    :param text:
        The text to be displayed.

    """
    print("{}".format(text))
    logger.debug("Output to user: {}".format(text))


def error_(text, description):
    """
    Displays error messages to the user and logs them.

    :param text:
        The error text to be displayed to the user.

    :param description:
        The error description for logging.

    """
    logger.error("Error: {}".format(description))
    print_(text)
