import unittest

import collect.converter.main as converter
import collect.test.util as util
from collect.converter.datatypes import StackEvent


class _BaseTest(util.BaseTest):
    """Base test class"""


# -----------------------------------------------------------------------------
# Tests
#

class StackTest(_BaseTest):
    """Class for testing data conversion of stack data"""
    def setUp(self):
        """Per-test set-up"""
        super().setUp()

    def tearDown(self):
        """Per-test tear-down"""
        super().tearDown()

    def check_create_stack_data(self, example, expected):
        filename = self._TEST_DIR + "create_stackdata_test"

        # Run converter on example input (implicitly tests hashability)
        converter.create_stack_data_unsorted(example, filename)

        # Get the generated output
        output = ""
        with open(filename, "r") as file_:
            for line in file_:
                output += line

        # Later should also test sorting in separate function

        # Check that we got the desired output
        self.assertEqual(output, expected)

    def test_create_stack_data_basic(self):
        """Check that counter works and the output has the desired form"""

        # Example input
        example = (StackEvent(("pname", "call1", "call2")), StackEvent((
            "pname", "call1", "call2")), StackEvent(("pname", "call3",
                                                     "call4")))

        # Expected ouput:
        expected = "pname;call1;call2 2\n" \
            "pname;call3;call4 1\n"

        self.check_create_stack_data(example, expected)

    @unittest.skipIf(not hasattr(converter, "create_stack_data"),
                     "Only do once sorting has been implemented.")
    def test_create_stack_data_sorted(self):
        """Check that the sorting works"""

        # Example input
        example = (StackEvent(("pname", "call3", "call4")), StackEvent((
            "pname", "call1", "call2")), StackEvent((
                "pname", "call1", "call2")))

        # Expected ouput:
        expected = "pname;call1;call2 2\n" \
                   "pname;call3;call4 1\n"

        self.check_create_stack_data(example, expected)


class EventTest(_BaseTest):
    """Class for testing data conversion of event data"""
    def setUp(self):
        """Per-test set-up"""
        super().setUp()

    def tearDown(self):
        """Per-test tear-down"""
        super().tearDown()
