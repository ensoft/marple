# -------------------------------------------------------------
# datatypes.py - intermediate form of data between collect and display
# June - August 2018 - Franz Nowak, Hrutvik Kanabar, Andrei Diaconu
# -------------------------------------------------------------

"""
Data types comprising the interface between the collect and display packages.

Usage: data types can be constructed using the constructors, or from a standard
string representation using the from_string method. The standard representation
is the one given by the __str__ method for each class, allowing a data type
object to be converted to standard representation using casting.

"""

__all__ = (
    'PointDatum',
    'StackDatum',
    'EventDatum',
)


import logging
import typing

from common import exceptions, consts

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


class EventDatum(typing.NamedTuple):
    """
    Represents a single scheduler event.

    .. attribute:: time:
        The timestamp of the event in CPU ticks.
    .. attribute:: type:
        The type of the event.
    .. attribute:: event_specific_datum:
        A tuple representing the data belonging to this particular event;
        The order of the arguments matters

    """
    time: int
    type: str
    specific_datum: tuple

    def __str__(self):
        """
        Converts an event to standard hashtag-separated value string format.

        The string does not have a line break at the end.
            Format: <time>consts.separator<type>consts.separator<datum>,
            where datum is a tuple
            Note that the fields cannot contain hashtags (and should not
            since they are events).

        """
        return consts.separator.join((str(self.time), self.type,
                                     str(self.specific_datum)))

    @classmethod
    def from_string(cls, string):
        """
        Converts a standard representation to a :class:`EventDatum` object.

        Tolerant to whitespace/trailing linebreaks.

        :param string:
            The string to convert.

        :raises:
            exceptions.DatatypeException
        :return:
            The resulting :class:`EventDatum` object.

        """
        try:
            time, type_, datum = string.strip().split(consts.separator)
            return EventDatum(time=int(time), type=type_,
                              specific_datum=eval(datum))
        except IndexError as ie:
            raise exceptions.DatatypeException(
                "EventDatum - not enough values in datatype string "
                "('{}')".format(string)) from ie
        except ValueError as ve:
            raise exceptions.DatatypeException(
                "EventDatum - could not convert datatype string "
                "('{}')".format(string)) from ve


class PointDatum(typing.NamedTuple):
    """
    Represents a single 2D datapoint, potentially with added info.

    .. attribute:: x:
        The independent variable value.
    .. attribute:: y:
        The dependent variable value.
    .. attribute:: info:
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
        Converts a standard representation into a :class:`PointDatum` object.

        Tolerant to whitespace/trailing linebreaks.

        :param string:
            The string to convert.

        :raises:
            exceptions.DatatypeException
        :return:
            The resulting :class:`PointDatum` object.

        """
        try:
            x, y, info = string.strip().split(",")
            return PointDatum(x=float(x), y=float(y), info=info)
        except IndexError as ie:
            raise exceptions.DatatypeException(
                "PointDatum - not enough values in datatype string "
                "('{}')".format(string)) from ie
        except ValueError as ve:
            raise exceptions.DatatypeException(
                "PointDatum - could not convert datatype string "
                "('{}')".format(string)) from ve


class StackDatum(typing.NamedTuple):
    """
    Represents a single stack.

    .. attribute:: weight:
        The relative weighting of the stack in the data.
    .. attribute:: stack:
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
        return ("{}" + consts.separator + "{}").\
            format(self.weight, ";".join(self.stack))

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_string(cls, string):
        """
        Converts a standard representation into a :class:`StackDatum` object.

        Tolerant to whitespace/trailing linebreaks.

        :param string:
            The string to convert.

        :raises:
            exceptions.DatatypeException
        :return:
            The resulting :class:`StackDatum` object.

        """
        try:
            weight, stack = string.strip().split(consts.separator)
            stack_tuple = tuple(stack.split(';'))
            return StackDatum(weight=int(weight), stack=stack_tuple)
        except ValueError as ve:
            raise exceptions.DatatypeException(
                "StackDatum - could not convert datatype string "
                "('{}')".format(string)) from ve


class StackData:
    class DataOptions(typing.NamedTuple):
        """
        - weight_units: the units for the weight (calls, bytes etc)

        """
        weight_units: str

    def __init__(self, datum_generator, start, end, interface, weight_units):
        self.datum_generator = datum_generator()
        self.start = start
        self.end = end
        self.interface = interface
        self.datatype = "stack"
        self.data_options = {
            'weight_units': weight_units,
        }

    def header_to_dict(self):
        header_dict = {
            "start": self.start,
            "end": self.end,
            "interface": self.interface,
            "datatype": self.datatype,
            "data_options": self.data_options,
        }
        return header_dict


class EventData:
    def __init__(self, datum_generator, start, end, interface):
        self.datum_generator = datum_generator()
        self.start = start
        self.end = end
        self.interface = interface
        self.datatype = "event"

    def header_to_dict(self):
        header_dict = {
            "start": self.start,
            "end": self.end,
            "interface": self.interface,
            "datatype": self.datatype,
        }
        return header_dict


class PointData:
    class DataOptions(typing.NamedTuple):
        """
        - x_label: label for the x axis;
        - x_units: units for the x axis;
        - y_label: label for the y axis;
        - y_units: uni
        """
        x_label: str
        y_label: str
        x_units: str
        y_units: str

    def __init__(self, datum_generator, start, end, interface, x_label,
                 x_units, y_label, y_units):
        self.datum_generator = datum_generator()
        self.start = start
        self.end = end
        self.interface = interface
        self.datatype = "point"
        self.data_options = {
            'x_label': x_label,
            'x_units': x_units,
            'y_label': y_label,
            'y_units': y_units,
        }

    def header_to_dict(self):
        header_dict = {
            "start": self.start,
            "end": self.end,
            "interface": self.interface,
            "datatype": self.datatype,
            "data_options": self.data_options
        }
        return header_dict
