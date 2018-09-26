# --------------------------------------------------------------------
# exceptions.py - custom exceptions
# June - September 2018 - Franz Nowak, Andrei Diaconu, Hrutvik Kanabar
# --------------------------------------------------------------------

"""Custom exceptions"""


class NotSupportedException(Exception):
    """Exception for when an interface is not suppported by the target kernel"""
    def __init__(self, message, required_kernel):
        """
        Init the error class

        :param message:
            the error message.
        :param required_kernel:
            the required kernel to run a collecter.

        """
        super().__init__(message)
        self.required_kernel = required_kernel


class DatatypeException(Exception):
    """Exception for errors relating to the datatypes in common.datatypes"""
    def __init__(self, message):
        """
        Init the error class

        :param message:
            the error message.

        """
        message = "Error in common.datatypes: " + message
        super().__init__(message)


class SubprocessedErorred(Exception):
    """Exception that is raised if during collection a subprocess errored"""
    def __init__(self, message):
        """
        Init the error class

        :param message:
            the error message.

        """
        super().__init__(message)
