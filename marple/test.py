# -------------------------------------------------------------
# test.py - Runs marple tests
# Sep 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

import pytest
from pylint import epylint as lint
import argparse
import sys
import os

marple_dir = os.path.dirname(__file__) + "/"
collect_dir = marple_dir + "collect"
display_dir = marple_dir + "display"
common_dir = marple_dir + "common"


class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


def main():
    # Parse args
    parser = argparse.ArgumentParser(
        prog="marple_test",
        description="Test suite for marple.")
    parser.add_argument("-w", "--warn", action="store_true",
                        help="display all Pylint warnings.")
    parsed = parser.parse_args(sys.argv[1:])

    pylint_args = [
        collect_dir, display_dir, common_dir,
        '--rcfile={}pylintrc.txt'.format(marple_dir),
        '--ignore=tools'
    ]

    if not parsed.warn:
        pylint_args.append('-E')

    pylint_args_string = " ".join(pylint_args)

    pytest_args = [
        '--cov={}'.format(marple_dir),
        '--cov-config={}.coveragerc'.format(marple_dir),
        collect_dir,
        display_dir,
        common_dir,
    ]

    print(color.BOLD + color.PURPLE + 'Starting Pytest:' + color.END + color.END)
    pytest_ret = pytest.main(pytest_args)
    if pytest_ret:
        exit(pytest_ret)

    print(color.BOLD + color.PURPLE + 'Finished Pytest.' + color.END + color.END)
    print("")

    print(color.BOLD + color.PURPLE +
          'Starting Pylint: warnings are ' + ('on' if parsed.warn else 'off') +
          color.END + color.END)
    pylint_ret = lint.py_run(pylint_args_string)
    if pylint_ret and not parsed.warn:
        exit(pylint_ret)
    print(color.BOLD + color.PURPLE + 'Finished Pylint.' + color.END + color.END)


if __name__ == "__main__":
    main()