import os
import shutil
import unittest
from unittest import mock

from common import file
from display.treemap import Treemap


class TreemapTest(unittest.TestCase):
    """Class for testing the treemap module and its helper functions"""
    _TEST_DIR = "/tmp/marple-test/"

    def setUp(self):
        """Per-test set-up"""
        os.makedirs(self._TEST_DIR, exist_ok=True)

    def tearDown(self):
        """Per-test tear-down"""
        shutil.rmtree(self._TEST_DIR)

    def _get_output(self, inpt):
        csv = self._TEST_DIR + "csv"
        stack = self._TEST_DIR + "stack"

        with open(stack, "w") as st:
            st.write(inpt)

        Treemap._generate_csv(stack, csv)

        with open(csv, "r") as file_:
            return file_.read()

    def test_create_treemap_csv_multidigit(self):
        """
        Tests multidigit weight values

        """
        # The expected output
        expected = "value;1;2;3\n" \
                   "00000;pname;call1;call2\n" \
                   "000000000;pname;call3;call4\n"

        # Get the output from a collapsed stack (first line in inpt is the
        # empty header
        inpt = "{}\n" \
               "00000#pname;call1;call2\n" \
               "000000000#pname;call3;call4\n"
        outpt = self._get_output(inpt)

        # Check that we got the desired output
        self.assertEqual(outpt, expected)

    def test_create_treemap_csv_different_stack_lengths(self):
        """
        Again, tests multidigit weights, now with bigger input

        """
        # The expected output
        expected = "value;1;2;3;4;5;6\n" \
                   "00000;pname;call1;call2;call3;call4;call5\n" \
                   "000000000;pname;call1;call2\n" \
                   "000;pname;call1;call2;call3"

        # Generate a treemap csv from a collapsed stack (first line in inpt
        # is the empty header
        inpt = "{}\n" \
               "00000#pname;call1;call2;call3;call4;call5\n" \
               "000000000#pname;call1;call2\n" \
               "000#pname;call1;call2;call3"
        out = self._get_output(inpt)

        # Check that we got the desired output
        self.assertEqual(out, expected)

    def test_corrupted_file(self):
        """
        Tests if corrupted files are handled correctly (the function should)
        rise a ValueError

        """
        # First line is the empty header
        inpt = "{}\n" \
               "2j35p235"
        with self.assertRaises(ValueError):
            self._get_output(inpt)

    @mock.patch("os.environ")
    @mock.patch("display.treemap.Treemap._generate_csv", return_value=1000)
    @mock.patch("util.d3plus.d3IpyPlus.from_csv", return_value="")
    @mock.patch("subprocess.Popen")
    @mock.patch("util.d3plus.d3IpyPlus.TreeMap.dump_html", return_value="")
    def test_show_function(self, mock_dump, mock_popen, mock_from_csv,
                           mock_gen_csv, os_mock):
        """
        Tests the right parameters for various functions used by the show
        function

        :param mock_dump: mock for dump_html
        :param mock_popen: mock for popen
        :param mock_from_csv: mock for csv
        :param mock_gen_csv: mock for _generate_csv
        :param os_mock: mock for environ
        :return:
        """
        inp = self._TEST_DIR + "in"
        out = file.DisplayFileName(given_name=self._TEST_DIR + "out")
        with open(inp, "w") as c:
            c.write("")
        with open(str(out), "w") as s:
            s.write("")
        tm = Treemap(25, inp, out)
        tm.show()

        # call_args: tuple where:
        #               - first field has all the ordered arguments;
        #               - second field has all the named arguments;
        # Right file
        self.assertEqual(mock_gen_csv.call_args[0][0], inp)
        # Right columns, also implies right ids (since they are the same
        # but without the 'value' field
        self.assertEqual(mock_from_csv.call_args[1]['columns'],
                         ["value"] + [str(x) for x in
                                      range(1, mock_gen_csv.return_value + 1)])
