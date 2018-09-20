# -------------------------------------------------------------
# error_acc.py - module that accumulates errors
# September 2018 - Andrei Diaconu
# -------------------------------------------------------------

"""
Module that acts as a global error collector for the subprocesses

It accumulates the errors from the collect modules that have subprocesses that
exit with a non-zero return code (so they resulted in an error, no data was
collected

"""

# Set where the errored interfaces are added
errored_collecters = set()
