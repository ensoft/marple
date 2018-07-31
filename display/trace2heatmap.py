# -------------------------------------------------------------
# trace2heatmap.py - interacts with Brendan Gregg's heatmap tool
# July 2018 - Hrutvik Kanabar
# -------------------------------------------------------------
"""
Interacts with Brendan Gregg's heatmap tool.

Runs the relevant Perl scripts from Brendan Gregg's trace2heatmap tool.

"""
import os
import subprocess

DISPLAY_DIR = str(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__)))) + "/"

HEATMAP_SCRIPT = DISPLAY_DIR + "util/HeatMap/trace2heatmap.pl"

from common import output

def make(in_filename, out_filename):
    """
    Uses Brendan Gregg's trace2heatmap tool to convert latency data to a heatmap.

    :param in_filename:
        The input data file.
    :param out_filename:
        The output heatmap image file.

    """
    with open(out_filename, "w") as out:
        awk = subprocess.Popen(["awk", "$1 ~ /^[0-9]/ { print $2, $9 }", in_filename],
                               stdout=subprocess.PIPE)

        subprocess.Popen([HEATMAP_SCRIPT, "--unitstime=s", "--unitslabel=s", "--steplat=1", "--maxlat=20", "--grid",
                         "--title='Block I/O Latency Heat Map'"], stdin=awk.stdout, stdout=out)


def show(image):
    """
    Uses firefox to display the heatmap.

    :param image:
        The image file containing the heatmap.

    """
    username = os.environ['SUDO_USER'] #@@@ TODO test this
    subprocess.call(["su", "-", "-c",  "firefox " + DISPLAY_DIR + image,
                     username])
