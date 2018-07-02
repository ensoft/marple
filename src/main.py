#!/usr/bin/env python3

import sys
import os
import datetime
import logging

from . import controller

logging.basicConfig("/var/log/leap/"
                    + datetime.date + datetime.time + os.getpid()
                    + ".log")
logger = logging.getLogger('leap-log')

if __name__ == "__main__":
    # Call main function with command line arguments
    # Excluding argv[0] (program name)
    controller.main(sys.argv[1:])
