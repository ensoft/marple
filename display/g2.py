# -------------------------------------------------------------
# flamegraph.py - interacts with the flame g2 tool
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------
"""
Interacts with the g2 tool.

Issues a command to start the necessary scripts in Dave Barach's g2 tool

"""
import logging
import os
import subprocess

from common import util
from common import file

logger = logging.getLogger(__name__)
logger.debug('Entered module: {}'.format(__name__))
logger.setLevel(logging.DEBUG)

DISPLAY_DIR = str(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__)))) + "/"


@util.log(logger)
def show(cpel_data):
    """
    Calls g2 to show a track separated graph

    :param cpel_data:
        The name of the CPEL file containing the data to be displayed.

    """
    tmp = file.TempFileName()
    with open(cpel_data, "rb") as read:
        read.readline()
        data = read.read()

    with open(str(tmp), "wb") as write:
        write.write(data)

    subprocess.call(["vpp/build-root/install-native/g2/bin/g2", "--cpel-input",
                     str(tmp)])
