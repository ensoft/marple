# -------------------------------------------------------------
# exceptions.py - custom exceptions
# June-July 2018 - Franz Nowak
# July 2018 - Andrei Diaconu
# -------------------------------------------------------------

"""Custom exceptions"""


class AbortedException(Exception):
    """Exception for when the program is aborted by decision of the user"""

class NotSupportedException(Exception):
    """Exception for when an interface is not suppported by the target kernel"""
    def __init__(self, message, required_kernel):
        super.__init__(message)
        self.required_kernel = required_kernel
