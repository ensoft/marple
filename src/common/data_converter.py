# -------------------------------------------------------------
# controller.py - user interface, parses and applies commands
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Converts data created by lower level modules
to a format that can be used by displaying tools

"""


def to_g2(filename, parser):
    """
    Convert data to CPEL format for g2

    Takes an input file and a format and creates a file
    readable by the vpp/g2 program

    """

    # Stub
    pass


def example_parser(filename):
    with open(filename, "r") as f:
        for line in f:
            data = line.split()
            if type(data[0]) != int: # and other checks
                raise IOError("file is int the wrong format!")
                exit()
            create_event()


def to_flame():
    """
    Convert data into the format required by Brendan Greggs flame graph tool

    """
    # Stub
    pass
