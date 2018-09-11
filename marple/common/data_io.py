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
    'Writer',
    'Reader'
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
    specific_datum: dict
    connected: list
    # of tuples of same length, connected[i][0] is the
    # source and connected[i][1] is its destionation

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
                                                  str(self.specific_datum),
                                                  str(self.connected)))

    @staticmethod
    def from_string(string):
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
            time, type_, datum, connected = \
                string.strip().split(consts.datum_field_separator)
            return EventDatum(time=int(time), type=type_,
                              specific_datum=eval(datum),
                              connected=eval(connected))
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

    @staticmethod
    def from_string(string):
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

    @staticmethod
    def from_string(string):
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

    datum_class = None

    DEFAULT_OPTIONS = DataOptions()

    def __init__(self, datum_generator, start_time, end_time,
                 interface, data_options=DEFAULT_OPTIONS):
        self.datum_generator = datum_generator
        self.start_time = start_time
        self.end_time = end_time
        self.interface = interface
        self.datatype = None
        self.data_options = data_options

    def header_dict(self):
        header_dict = {
            "start time": str(self.start_time),
            "end time": str(self.end_time),
            "interface": self.interface.value,
            "datatype": self.datatype,
            "data options": self.data_options._asdict(),
        }
        return header_dict

    def to_string(self):
        yield json.dumps(self.header_dict())

        for datum in self.datum_generator:
            yield str(datum)

    @classmethod
    def from_string(cls, string):
        split = string.strip().split('\n')
        header = json.loads(split[0])

        datum_generator = (cls.datum_class.from_string(line)
                           for line in split[1:])

        return cls(datum_generator, header['start time'], header['end time'],
                   consts.InterfaceTypes(header['interface']),
                   cls.DataOptions(**(header['data options'])))


class StackData(Data):
    datum_class = StackDatum

    class DataOptions(typing.NamedTuple):
        """
        - weight_units: the units for the weight (calls, bytes etc)

        """
        weight_units: str

    DEFAULT_OPTIONS = DataOptions(weight_units="samples")

    @util.Override(Data)
    def __init__(self, datum_generator, start, end, interface,
                 data_options=DEFAULT_OPTIONS):
        super().__init__(datum_generator, start, end, interface, data_options)
        self.datatype = consts.Datatypes.STACK.value


class EventData(Data):
    datum_class = EventDatum

    class DataOptions(typing.NamedTuple):
        pass

    DEFAULT_OPTIONS = DataOptions()

    @util.Override(Data)
    def __init__(self, datum_generator, start, end, interface,
                 data_options=DEFAULT_OPTIONS):
        super().__init__(datum_generator, start, end, interface, data_options)
        self.datatype = consts.Datatypes.EVENT.value


class PointData(Data):
    datum_class = PointDatum

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

    def __init__(self, datum_generator, start, end, interface,
                 data_options=DEFAULT_OPTIONS):
        super().__init__(datum_generator, start, end, interface, data_options)
        self.datatype = consts.Datatypes.POINT.value


class Writer:

    def __init__(self, filename):
        """
        Initialises a writer object.

        Creates a blank metaheader, and stores the filename.
        Also initialises a file_length variable, to track the current length
        of the file in lines.

        :param filename:
            The desired output filename.

        """
        self.filename = filename
        self.metaheader = dict()

    def __enter__(self):
        """ Context manager for writer. """
        self.file = open(self.filename, 'w+', encoding='utf-8')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Close the file resource. """

        # Read data sections from beginning of file
        self.file.seek(0)
        sections = self.file.read()

        # Write metaheader + data sections to file
        self.file.seek(0)
        self._write_metaheader()
        self.file.write(sections)

        # Close file
        self.file.close()

    def _write_metaheader(self):
        """
        Write the metaheader to the file.

        """
        metaheader = json.dumps(self.metaheader) + "\n"
        self.file.write(metaheader)

    def _write_section(self, index, data):
        """
        Write a single section in a standard format file.

        Appends the section to the current standard format file.
        Includes the section separator.

        :param data:
            A StackData, EventData, or PointData object.

        """
        # Write to file, keep track of start and end
        start_byte = self.file.tell()
        for line in data.to_string():
            self.file.write(line + "\n")
        self.file.write(consts.data_separator)
        end_byte = self.file.tell()

        # Update metaheader
        header = data.header_dict()
        header["start byte"] = start_byte
        header["end byte"] = end_byte
        self.metaheader[index] = header

    @util.log(logger)
    def write(self, data_objs):
        """
        Write the data to a standard format file.

        Write a metaheader, and then sections of data.

        :param data_objs:
            An iterator of data objects.

        """
        for index, data in enumerate(data_objs):
            self._write_section(index, data)


class Reader:

    def __init__(self, filename):
        """
        Initialises a reader object.

        Stores the filename.

        :param filename:
            The input filename.

        """
        self.filename = filename

    def __enter__(self):
        """
        Context manager for reader.

        Stores the metaheader for future usage.

        """
        self.file = open(self.filename, 'r', encoding='utf-8')
        self.metaheader = json.loads(self.file.readline().strip())
        self.offset = self.file.tell()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Close the file resource. """
        self.file.close()

    def _get_interface_index(self, interface):
        for index, header in self.metaheader.items():
            if header['interface'] == interface:
                return index

    def _get_data_from_section(self, index):
        try:
            header = self.metaheader[str(index)]
        except KeyError as ke:
            raise exceptions.DatatypeException(
                "Metaheader error: entry no. {} not found!".format(index))\
                from ke
        self.file.seek(self.offset + header["start byte"])
        num_bytes = header["end byte"] - header["start byte"]
        section = self.file.read(num_bytes)

        datatype = header['datatype']

        if datatype == consts.Datatypes.EVENT.value:
            result = EventData.from_string(section)
        elif datatype == consts.Datatypes.POINT.value:
            result = PointData.from_string(section)
        elif datatype == consts.Datatypes.STACK.value:
            result = StackData.from_string(section)
        else:
            raise exceptions.DatatypeException(
                "Header error: datatype '{}' not recognised!".format(datatype))

        return result

    def get_interface_from_index(self, index):
        try:
            header = self.metaheader[str(index)]
        except KeyError as ke:
            raise exceptions.DatatypeException(
                "Metaheader error: entry no. {} not found!".format(index)) \
                from ke

        return header['interface']

    def get_all_interface_names(self):
        interfaces = [header['interface']
                      for _, header in self.metaheader.items()]
        assert len(interfaces) == len(set(interfaces))  # no duplicates
        return set(interfaces)

    def get_header_list(self):
        format_str = "{:>8.8}. {:12.12} {:10.10} {:30.30} {:30.30}"
        headers = [
            format_str
            .format(index, header['interface'], header['datatype'],
                    header['start time'], header['end time'])
            for index, header in self.metaheader.items()
        ]
        return [format_str.format("Entry no", "Subcommand", "Datatype",
                                  "Start time", "End time")] + headers

    def get_interface_data(self, *interfaces):
        for interface in interfaces:
            index = self._get_interface_index(interface)
            data = self._get_data_from_section(index)
            yield data
