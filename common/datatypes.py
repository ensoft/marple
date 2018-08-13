# -------------------------------------------------------------
# datatypes.py - intermediate form of data between collect and display
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

"""
Data types comprising the interface between the collect and display packages.

Usage: data types can be constructed using the constructors, or from a standard
string representation using the from_string method. The standard representation
is the one given by the __str__ method for each class, allowing a data type
object to be converted to standard representation using casting.

"""

__all__ = (
    'Datapoint',
    'StackData',
    'SchedEvent',
)


import typing
import logging

from common import exceptions

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


class SchedEvent(typing.NamedTuple):  # @@@ TODO make this more general
    """
    Represents a single scheduler event.

    .. atrribute:: time:
        The timestamp of the event in Cpu ticks.
    .. atrribute:: type:
        The type of the event.
    .. atrribute:: track:
        The track that the event belongs to (e.g. cpu core, process, ...)
    .. atrribute:: datum:
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
        return ",".join((str(self.time), self.type, self.track, self.datum))

    @classmethod
    def from_string(cls, string):
        """
        Converts a standard representation to a :class:`SchedEvent` object.

        Tolerant to whitespace/trailing linebreaks.

        :param string:
            The string to convert.

        :raises:
            exceptions.DatatypeException
        :return:
            The resulting :class:`SchedEvent` object.

        """
        try:
            time, type, track, datum = string.strip().split(",")
            return SchedEvent(time=int(time), type=type,
                              track=track, datum=datum)
        except IndexError as ie:
            raise exceptions.DatatypeException(
                "SchedEvent - not enough values in datatype string "
                "('{}')".format(string)) from ie
        except ValueError as ve:
            raise exceptions.DatatypeException(
                "SchedEvent - could not convert datatype string "
                "('{}')".format(string)) from ve


class Datapoint(typing.NamedTuple):
    """
    Represents a single 2D datapoint, potentially with added info.

    .. atrribute:: x:
        The independent variable value.
    .. atrribute:: y:
        The dependent variable value.
    .. atrribute:: info:
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
        return ",".join((str(self.x), str(self.y), self.info))

    @classmethod
    def from_string(cls, string):
        """
        Converts a standard representation into a :class:`Datapoint` object.

        Tolerant to whitespace/trailing linebreaks.

        :param string:
            The string to convert.

        :raises:
            exceptions.DatatypeException
        :return:
            The resulting :class:`Datapoint` object.

        """
        try:
            x, y, info = string.strip().split(",")
            return Datapoint(x=float(x), y=float(y), info=info)
        except IndexError as ie:
            raise exceptions.DatatypeException(
                "Datapoint - not enough values in datatype string "
                "('{}')".format(string)) from ie
        except ValueError as ve:
            raise exceptions.DatatypeException(
                "Datapoint - could not convert datatype string "
                "('{}')".format(string)) from ve


class StackData(typing.NamedTuple):
    """
    Represents a single stack.

    .. atrribute:: weight:
        The relative weighting of the stack in the data.
    .. atrribute:: stack:
        The stack as a tuple of strings (<baseline>, <stackline>. ...)

    """
    # Could have more attributes if needed
    weight: int
    stack: typing.Tuple[str, ...]

    def __str__(self):
        """
        Converts a stack datum to standard comma-separated value string format.

        The string does not have a line break at the end.
        Format: <weight>,<baseline>;<stackline1>;<stackline2>;...
        Note that baselines and stacklines should not contain
        commas or semicolons.

        """
        return "{},{}".format(self.weight, ";".join(self.stack))

    @classmethod
    def from_string(cls, string):
        """
        Converts a standard representation into a :class:`StackData` object.

        Tolerant to whitespace/trailing linebreaks.

        :param string:
            The string to convert.

        :raises:
            exceptions.DatatypeException
        :return:
            The resulting :class:`StackData` object.

        """
        try:
            weight, stack = string.strip().split(",")
            stack_tuple = tuple(stack.split(';'))
            return StackData(weight=int(weight), stack=stack_tuple)
        except ValueError as ve:
            raise exceptions.DatatypeException(
                "StackData - could not convert datatype string "
                "('{}')".format(string)) from ve
