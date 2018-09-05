# -------------------------------------------------------------
# exceptions.py - custom exceptions
# June-July 2018 - Franz Nowak, Andrei Diaconu, Hrutvik Kanabar
# -------------------------------------------------------------

"""Custom exceptions"""


class NotSupportedException(Exception):
    """Exception for when an interface is not suppported by the target kernel"""
    def __init__(self, message, required_kernel):
        super().__init__(message)
        self.required_kernel = required_kernel


class DatatypeException(Exception):
    """Exception for errors relating to the datatypes in common.datatypes"""
    def __init__(self, message):
        message = "Error in common.datatypes: " + message
        super().__init__(message)
