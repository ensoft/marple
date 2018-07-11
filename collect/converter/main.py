# -------------------------------------------------------------
# converter/main.py - Saves data objects into a file.
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Saves data objects into a file.

Gets the data that was collected by an interface module and converted into
formatted objects and writes them into a file that was provided by the user.

"""
from collections import Counter


def create_stack_data(generator, filename):
    """
    Count, sort and saves the stack data from the generator into a file.

    :param generator:
        The generator of stack objects
    :param filename:
        The name of the file into which to store the output.

    """
    # Count stack occurrences
    cnt = Counter()
    for line in generator:
        cnt[line] += 1

    # @Sort by keys (recursively by ascending index)
    pass

    # @Write to file
    pass


def create_cpu_event_data(generator, filename):
    """
    Saves the event data from the generator into a file.

    :param generator:
        The generator of SchedEvent objects
    :param filename:
        The name of the file into which to store the output.

    """

    # @Write to file
    pass
