# -------------------------------------------------------------
# data_io.py - intermediate form of data between collect and display
# June - August 2018 - Franz Nowak, Hrutvik Kanabar, Andrei Diaconu
# -------------------------------------------------------------

"""
Handles data input and output for MARPLE.

Standard datatypes (PointDatum, StackDatum, and EventDatum) are defined.
Collections of data (including header info) are also defined - these are
PointData, StackData, and EventData.
Lastly, methods for writing and reading these to standard MARPLE data files
are defined.

Each datatype has __str__ and from_string methods, allowing for simple
conversion to and from standard strings.
Each collection of data has a method to convert the header to a string.

MARPLE standard data files are as follows:
<header 1>
<collection of data
...
>
<blank line>
<header 2>
<
collection of data
...
>
<blank line>
...

Where each collection of data consists of a single datapoint on each line.



"""

__all__ = (
    'PointDatum',
    'StackDatum',
    'EventDatum',
    'StackData',
    'PointData',
    'EventData',
    'write',
    'read_header',
    'read_until_line'
)

import json
import logging
import typing

from marple.common import exceptions, consts, util

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
        return consts.datum_field_separator.join((str(self.time), self.type,
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
            time, type_, datum = string.strip().split(consts.datum_field_separator)
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
        return consts.datum_field_separator.join((str(self.weight), ';'.join(self.stack)))

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
            weight, stack = string.strip().split(consts.datum_field_separator)
            stack_tuple = tuple(stack.split(';'))
            return StackDatum(weight=int(weight), stack=stack_tuple)
        except ValueError as ve:
            raise exceptions.DatatypeException(
                "StackDatum - could not convert datatype string "
                "('{}')".format(string)) from ve


class Data:
    class DataOptions(typing.NamedTuple):
        pass

    DEFAULT_OPTIONS = DataOptions()

    def __init__(self, datum_generator, start_time, end_time, interface):
        self.datum_generator = datum_generator
        self.start_time = start_time
        self.end_time = end_time
        self.interface = interface
        self.datatype = None
        self.data_options = {}

    def header_dict(self):
        header_dict = {
            "start": str(self.start_time),
            "end": str(self.end_time),
            "interface": self.interface.value,
            "datatype": self.datatype,
            "data_options": self.data_options,
        }
        return header_dict

    def to_string(self):
        yield json.dumps(self.header_dict())

        for datum in self.datum_generator:
            yield str(datum)


class StackData(Data):
    class DataOptions(typing.NamedTuple):
        """
        - weight_units: the units for the weight (calls, bytes etc)

        """
        weight_units: str
    DEFAULT_OPTIONS = DataOptions("samples")

    @util.Override(Data)
    def __init__(self, datum_generator, start, end, interface, weight_units):
        super().__init__(datum_generator, start, end, interface)
        self.datatype = "stack"
        self.data_options = {
            'weight_units': weight_units,
        }


class EventData(Data):
    @util.Override(Data)
    def __init__(self, datum_generator, start, end, interface):
        super().__init__(datum_generator, start, end, interface)
        self.datatype = "event"


class PointData(Data):
    class DataOptions(typing.NamedTuple):
        """
        - x_label: label for the x axis;
        - x_units: units for the x axis;
        - y_label: label for the y axis;
        - y_units: units for the y axis;
        """
        x_label: str
        y_label: str
        x_units: str
        y_units: str
    DEFAULT_OPTIONS = DataOptions("x label", "y label", "x units", "y units")

    def __init__(self, datum_generator, start, end, interface, x_label,
                 x_units, y_label, y_units):
        super().__init__(datum_generator, start, end, interface)
        self.datatype = "point"
        self.data_options = {
            'x_label': x_label,
            'x_units': x_units,
            'y_label': y_label,
            'y_units': y_units,
        }


@util.log(logger)
def write(data, filename):
    """
    Write standard datatypes to a standard format file.

    Note that the file is appended to, rather than overwritten.

    :param data:
        A StackData, EventData, or PointData object
    :param filename:
        The output file name

    """
    with open(filename, "a") as out:
        for line in data.to_string():
            out.write(line + "\n")
        out.write(consts.data_separator)


@util.log(logger)
def read_header(file_object):
    """
    Read the header of the file (its first line).

    If the header is not a valid JSON on a single line, an error is thrown.
    If at the end of a file, None is returned.

    :param file_object:
        The input file object.
    :return:
        The dictionary representation of the file header.
    :raises:
        json.JSONDecodeError if the header is invalid.

    """
    header_str = file_object.readline().strip()
    if not header_str:  # end of a file
        return None

    try:
        header_dict = json.loads(header_str)
        return header_dict
    except json.JSONDecodeError as jse:
        jse.msg = "Malformed JSON header!"
        raise jse


@util.log(logger)
def read_until_line(file_object, stop_line):
    """
    Lazily read from the file until a certain line.

    If the end of the file is encountered, the results so far are returned.

    :param file_object:
        The input file to read.
        Reading continues from the current file pointer position.
    :param stop_line:
        The line at which to stop.
    :return:
        Yields single lines from the file.

    """
    line = file_object.readline()
    while line not in (stop_line, ''):
        yield line
        line = file_object.readline()
