# -------------------------------------------------------------
# treemap.py - Generates a treemap representation of the data
# July 2018 - Andrei Diaconu, Hrutvik Kanabar
# -------------------------------------------------------------
"""
Displays the collected data as a treemap

"""

__all__ = (
    'Treemap'
)

import logging
import os
import subprocess
from typing import NamedTuple

from marple.common import (
    file,
    util,
    consts,
    data_io
)
from marple.display.interface.generic_display import GenericDisplay
from marple.display.tools.d3plus import d3IpyPlus as d3

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


class Treemap(GenericDisplay):
    # @TODO: Add more options (look at how the treemap is initialised)
    class DisplayOptions(NamedTuple):
        """
        Options:
            - depth: the maximum depth of the treemap (max number of elements
                     in a stack);
        """
        depth: int
    _DEFAULT_OPTIONS = DisplayOptions(depth=25)

    def __init__(self, data, out,
                 data_options=data_io.StackData.DEFAULT_OPTIONS,
                 display_options=_DEFAULT_OPTIONS):
        """
        Constructor for the Treemap.

        :param data:
            A generator that returns the data for the section we want to
            display as a treemap
        :param out:
            The output file where the image will be saved as an instance
            of the :class:`DisplayFileName`.
        :param data_options: object of the class specified in each of the `Data`
                             classes, containig various data options to be used
                             in the display class as labels or info
        :param display_options: display related options that are meant to make
                                the display option more customizable

        """
        # Initialise the base class
        super().__init__(data_options, display_options)

        self.data = data
        # Setting the right extension and getting the path of the outp
        out.set_options("treemap", "html")
        self.output = str(out)

    @util.log(logger)
    def _generate_csv(self, out_file):
        """
        Creates a semicolon separated file using the data in self.data.
        The output format will be:
            - first line: Represents the columns (header); first column will
                          represent the value of the stack line; the rest of the
                          columns will be numbers from 1 to the maximum stack
                          depth, representing the groups we use for creating the
                          hierarchies;
            - next lines: values of the above columns, separated by semicolons;
                          the values for the groups will be the function at that
                          depth; group priorities are from left to right,
                          so group 1 has a higher priority (will be displayed
                          over in the treemap) than group 2 (see bellow)
                          example: bytes;1;2;3 -- first row
                                   5;firefox;[unknown];libxul.so -- second row

        :param out_file: a semicolon separated file generated from the in_file;
                         expects an absolute path
        :raises ValueError: in case the file is not in an accepted format
        :returns max_depth: the maximum depth of the stack

        """

        with open(out_file, "w") as out_file:
            # Header of the csv; example: value;1;2;3;4;5...
            out_file.write(self.data_options.weight_units + ";" +
                           ";".join([str(i) for i in
                                     range(1, self.display_options.depth+1)]) +
                           "\n")

            for line in self.data:
                # If we do not have a separator between the weight and the
                # first element of the stack, raise error
                if line.count(consts.datum_field_separator) != 1:
                    raise ValueError(
                        "Invalid format of the file! Each line should "
                        "have the format weight{}... Line that "
                        "causes the problem {}".format(consts.datum_field_separator, line))

                # We replace the only consts.separator character with ';',
                # as requested by the d3 module that separates the weight from
                # the callstack
                call_stack = line.strip().replace(consts.datum_field_separator, ";", 1)
                sep = call_stack.split(';')
                # We write the obtained stack, but only to the specified depth
                out_file.write(';'.join(
                    sep[0:self.display_options.depth + 1]) + '\n')

    @util.Override(GenericDisplay)
    @util.log(logger)
    def show(self):
        """
        Displays the input stack as a treemap using the d3IpyPlus tool.

        Creates the ids and the columns that are passed in the treemap object,
        which is used to generate a html file that is to be displayed.
        """

        # Temp file for the csv file
        temp_file = str(file.TempFileName())
        self._generate_csv(temp_file)

        # Generate the ids we use for the hierarchies and the columns of the
        # input file
        ids = [str(i) for i in range(1, self.display_options.depth + 1)]
        cols = [self.data_options.weight_units] + ids

        # Retrieve data from the temporary file that holds the csv format
        # that d3 uses
        data = d3.from_csv(temp_file, ';', columns=cols)

        # Create the treemap with the supplied display options
        tmap = d3.TreeMap(id=ids[0:self.display_options.depth],
                          value=self.data_options.weight_units,
                          color=self.data_options.weight_units,
                          legend=True, width=700)
        with open(str(self.output), "w") as out:
            out.write(tmap.dump_html(data))

        username = os.environ['SUDO_USER']
        subprocess.call(["su", "-", "-c", "firefox " +
                         str(self.output), username])
