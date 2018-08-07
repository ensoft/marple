import struct
import unittest

import display.treemap as treemap

import display.test.util_display as util


class _BaseTest(util.BaseTest):
    """Base test class"""

# -----------------------------------------------------------------------------
# Tests


class TreemapTest(_BaseTest):
    """Class for testing the treemap module and its helper functions"""

    def test_create_treemap_csv_multidigit(self):
        csv = self._TEST_DIR + "create_treemap_csv"
        stack = self._TEST_DIR + "write_example_stack"

        # The expected output
        expected = "value;1;2;3\n" \
                   "00000;pname;call1;call2\n" \
                   "000000000;pname;call3;call4\n"

        # Generate a treemap csv from a collapsed stack
        inpt = "pname;call1;call2 00000\n" \
               "pname;call3;call4 000000000\n"
        with open(stack, "w") as st:
            st.write(inpt)

        treemap.generate_csv(stack, csv)

        outpt = ""
        with open(csv, "r") as file_:
            for line in file_:
                outpt += line

        # Check that we got the desired output
        self.assertEqual(outpt, expected)
