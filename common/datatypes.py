# -------------------------------------------------------------
# test_datatypes.py - intermediate form of data to be converted
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

"""
Data types comprising the interface between the
collect and display packages

"""

__all__ = (
    'Datapoint',
    'Datapoint.from_string',
    'StackData',
    'StackData.from_string',
    'SchedEvent',
    'SchedEvent.from_string'
)


from typing import NamedTuple
import logging

from common import (
    exceptions,
    util
)

logger = logging.getLogger(__name__)
logger.debug('Entered module: {}'.format(__name__))

class SchedEvent(NamedTuple):  # @@@ TODO make this more general
    """
    Represents a single scheduler event.
    :key time:
        The timestamp of the event in Cpu ticks.
    :key type:
        The type of the event.
    :key track:
        The track that the event belongs to (e.g. cpu core, process, ...)
    :key datum:
        The data belonging to this event, (e.g. process id etc, cpu ... )

    """
    time: int
    type: str
    track: str
    datum: str

    def __str__(self):
        """
        Converts an event to standard comma-separated value string format.
        The string does not have a line break at the end.
        Format: <time>,<type>,<track>,<datum>
        Note that the fields cannot contain commas.

        """
        result = str(self.time) + "," + self.type + "," + self.track + "," + \
                     self.datum
        return result

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_string(cls, string):
        """
        Converts a standard string representation of a scheduling event into
        a :class:`Sched` object.
        Can throw :class:`exceptions.DatatypeException`.
        Tolerant to whitespace/trailing linebreaks.

        :param string:
            The string to convert.
        :return:
            The resulting :class:`SchedEvent` object.

        """
        try:
            fields = string.strip().split(",")
            return SchedEvent(time=int(fields[0]), type=fields[1],
                              track=fields[2], datum=fields[3])
        except IndexError as ie:
            raise exceptions.DatatypeException(
                "SchedEvent - not enough values in datatype string "
                "('{}')".format(string)) from ie
        except ValueError as ve:
            raise exceptions.DatatypeException(
                "SchedEvent - could not convert datatype string "
                "('{}')".format(string)) from ve


class Datapoint(NamedTuple):
    """
    Represents a single 2D datapoint, potentially with added info.

    x:
        The independent variable value.
    y:
        The dependent variable value.
    info:
        Additional info for the datapoint.

    """
    x: float
    y: float
    info: str

    def __str__(self):
        """
        Converts a datapoint to standard comma-separated value string format.
        The string does not have a line break at the end.
        Format: <x>,<y>,<info>
        Note that the info field cannot contain commas. Use semicolons as
        separators if necessary.

        """
        result = str(self.x) + "," + str(self.y) + "," + self.info
        return result

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_string(cls, string):
        """
        Converts a standard string representation of a datapoint into
        a :class:`Datapoint` object.
        Can throw :class:`exceptions.DatatypeException`.
        Tolerant to whitespace/trailing linebreaks.

        :param string:
            The string to convert.
        :return:
            The resulting :class:`Datapoint` object.

        """
        try:
            fields = string.strip().split(",")
            return Datapoint(x=float(fields[0]), y=float(fields[1]),
                             info=fields[2])
        except IndexError as ie:
            raise exceptions.DatatypeException(
                "Datapoint - not enough values in datatype string "
                "('{}')".format(string)) from ie
        except ValueError as ve:
            raise exceptions.DatatypeException(
                "Datapoint - could not convert datatype string "
                "('{}')".format(string)) from ve


class StackData(NamedTuple):
    """
    Represents a single stack

    weight:
        The relative weighting of the stack in the data.
    stack:
        The stack as a tuple (<baseline>, <stackline>. ...)

    """
    # Could have more attributes if needed
    weight: int
    stack: tuple

    def __str__(self):
        """
        Converts a stack datum to standard comma-separated value string format.
        The string does not have a line break at the end.
        Format: <weight>,<baseline>;<stackline1>;<stackline2>;...
        Note that baselines and stacklines should not contain
        commas or semicolons.

        """
        result = str(self.weight) + "#"
        for stack_line in self.stack[:-1]:
            result += stack_line + ";"
        result += self.stack[-1]
        return result


    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_string(cls, string):
        """
        Converts a standard string representation of a stack datum into
        a :class:`StackData` object.
        Can throw :class:`exceptions.DatatypeException`.
        Tolerant to whitespace/trailing linebreaks.

        :param string:
            The string to convert.
        :return:
            The resulting :class:`StackData` object.

        """
        try:
            fields = string.strip().split("#")
            if len(fields) != 2:
                raise exceptions.DatatypeException(
                    "StackData - incorrect no. of values in datatype string")
            weight = int(fields[0])
            stack_list = fields[1].split(";")
            stack = tuple(stack_list)
            return StackData(weight=weight, stack=stack)
        except ValueError as ve:
            raise exceptions.DatatypeException(
                "StackData - could not convert datatype string "
                "('{}')".format(string)) from ve
