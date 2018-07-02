# -------------------------------------------------------------
# controller.py - user interface, parses and applies commands
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Displays output to the user and logs it.

Provides functions for normal print output and errors.
"""

import logging
logger = logging.getLogger("leap_log")


def print_output(text):
    """
    Displays normal output to the user and logs it.

    :param text:
        The text to be displayed.

    """
    print(text)
    logger.debug("output to user: {}".format(text))


def print_error(text, description):
    """
    Displays error messages to the user and logs them.

    :param text:
        The error text to be displayed to the user.

    :param description:
        The error description for logging.

    """
    logger.error("Error: {}".format(description))
    print_output(text)
