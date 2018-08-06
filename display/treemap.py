# -------------------------------------------------------------
# treemap.py - Generates a treemap representation of the data
# July 2018 - Andrei Diaconu
# -------------------------------------------------------------
"""
Displays the collected data as a treemap

"""

from util.d3plus import d3IpyPlus as d3
import subprocess
import os
import common.file as file

DISPLAY_DIR = str(os.path.dirname(os.path.dirname(os.path.realpath(
    __file__)))) + "/"
DEPTH = 25

__all__ = (
    'generate_csv',
    'show'
)


def generate_csv(in_file, out_file):
    """
    Creates a semicolon separated file from a stack parser output.
    The output format will be:
        - first line: Represents the columns (header); first column will
                      represent the value of the stack line; the rest of the
                      columns will be numbers from 1 to the maximum stack depth,
                      representing the groups we use for creating the
                      hierarchies;
        - next lines: values of the above columns, separated by semicolons; the
                      values for the groups will be the function at that depth;
                      example: value;1;2;3 -- first row
                               5;firefox;[unknown];libxul.so -- second row

    :param in_file: a collapsed stack produced by the stack parser; expects
                    an absolute path
    :param out_file: a semicolon separated file generated from the in_file;
                     expects an absolute path
    """
    with open(out_file, "w") as out_file:
        max_num_proc = 0
        with open(in_file, "r") as read_file:
            for line in read_file:
                if max_num_proc < line.count(';') + 1:
                    max_num_proc = line.count(';') + 1

        # Header of the csv
        out_file.write("value;")
        for i in range(1, max_num_proc + 1):
            out_file.write(str(i) + ";")
        out_file.write('\n')

        with open(in_file, "r") as read_file:
            for line in read_file:
                # Get rid of the newline char
                call_stack = line[:len(line) - 1]

                # Since the depths of the call stacks are variable,
                # we need the weights to be displayed at the beginning of
                # each line, so that we can use them as the value field for
                # the tree map. So we delete the number and prepend it to the
                # line.
                num = ""
                i = len(call_stack) - 1
                while call_stack[i] != ' ':
                    num += call_stack[i]
                    i -= 1
                # We deleted the number so we want to adjust the line
                call_stack = call_stack[:i]

                # Reverse the number since we read it backwards and prepend it
                num = num[::-1]
                call_stack = num + ';' + call_stack
                out_file.write(call_stack + '\n')
        return max_num_proc


def show(in_file, out_file):
    """
    Displays the input stack as a treemap using the d3IpyPlus tool. Because of
    the big loading times for big depths, we will use at most DEPTH levels

    :param in_file: a stack file
    :param out_file: an html file containing the treemap representation

    """

    # Temp file for the csv file
    temp_file = file.create_unique_temp_filename()
    max_num_proc = generate_csv(DISPLAY_DIR + in_file, temp_file)

    # Generate the ids we use for the hierarchies and the columns of the input
    # file
    ids = []
    for i in range(1, max_num_proc + 1):
        ids.append(str(i))
    cols = ["value"] + ids

    data = d3.from_csv(temp_file, ';', columns=cols)
    tmap = d3.TreeMap(id=ids[0:DEPTH], value="value", color="value",
                      legend=True, width=700)
    with open(DISPLAY_DIR + out_file, "w") as out:
        out.write(tmap.dump_html(data))

    username = os.environ['SUDO_USER']
    subprocess.call(["su", "-", "-c", "firefox " +
                     DISPLAY_DIR + out_file, username])