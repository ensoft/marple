import os
import shutil
import unittest
from unittest import mock

from marple.common import file, data_io, consts
from marple.display.interface import treemap


class TreemapTest(unittest.TestCase):
    """Class for testing the treemap module and its helper functions"""
    _TEST_DIR = "/tmp/marple-test/"

    # Set up blank treemap
    tmap = object.__new__(treemap.Treemap)

    tmap.display_options = treemap.Treemap.DisplayOptions(25)
    tmap.data_options = data_io.StackData.DataOptions("kb")
    tmap.data = iter(())
    tmap.output = file.DisplayFileName("file")

    def setUp(self):
        """Per-test set-up"""
        os.makedirs(self._TEST_DIR, exist_ok=True)

    def tearDown(self):
        """Per-test tear-down"""
        shutil.rmtree(self._TEST_DIR)

    def _get_output(self, data):
        csv = self._TEST_DIR + "csv"

        self.tmap.data = data
        self.tmap._generate_csv(csv)

        with open(csv, "r") as file_:
            return file_.read()

    def test_create_treemap_csv_multidigit(self):
        """
        Tests multidigit weight values

        """
        # The expected output
        expected = self.tmap.data_options.weight_units + ";" + \
                   ';'.join([str(i) for i in
                             range(1, self.tmap.display_options.depth + 1)]) + \
                   '\n' + \
                   "00000;pname;call1;call2\n" \
                   "000000000;pname;call3;call4\n"

        # Get the output from a collapsed stack (first line in inpt is the
        # empty header
        data = iter(("00000" + consts.datum_field_separator + "pname;call1;call2\n",
                     "000000000" + consts.datum_field_separator + "pname;call3;call4\n"))
        outpt = self._get_output(data)

        # Check that we got the desired output
        self.assertEqual(outpt, expected)

    def test_create_treemap_csv_different_stack_lengths(self):
        """
        Again, tests multidigit weights, now with bigger input

        """
        # The expected output
        expected = self.tmap.data_options.weight_units + ";" + \
                   ';'.join([str(i) for i in
                             range(1, self.tmap.display_options.depth + 1)]) + \
                   '\n' + \
                   "00000;pname;call1;call2;call3;call4;call5\n" \
                   "000000000;pname;call1;call2\n" \
                   "000;pname;call1;call2;call3\n"

        data = iter(("00000" + consts.datum_field_separator
                     + "pname;call1;call2;call3;call4;call5\n",
                     "000000000" + consts.datum_field_separator + "pname;call1;call2\n",
                     "000" + consts.datum_field_separator + "pname;call1;call2;call3"))

        out = self._get_output(data)

        # Check that we got the desired output
        self.assertEqual(out, expected)

    def test_corrupted_file(self):
        """
        Tests if corrupted files are handled correctly (the function should)
        rise a ValueError

        """
        # First line is the empty header
        data = iter(("Not a valid stackline"))
        with self.assertRaises(ValueError):
            self._get_output(data)

    @mock.patch("builtins.open")
    @mock.patch("os.environ")
    @mock.patch("marple.display.interface.treemap.Treemap._generate_csv")
    @mock.patch("marple.display.tools.d3plus.d3IpyPlus.from_csv", return_value="")
    @mock.patch("subprocess.Popen")
    @mock.patch("marple.display.tools.d3plus.d3IpyPlus.TreeMap.dump_html",
                return_value="")
    def test_show_function(self, mock_dump, mock_popen, mock_from_csv,
                           mock_gen_csv, os_mock, mock_open):
        """
        Tests the right parameters for various functions used by the show
        function

        :param mock_dump: mock for dump_html
        :param mock_popen: mock for popen
        :param mock_from_csv: mock for csv
        :param mock_gen_csv: mock for _generate_csv
        :param os_mock: mock for environ
        :return:
        # """
        self.tmap.show()

        # Right columns, also implies right ids (since they are the same
        # but without the 'value' field
        self.assertEqual(mock_from_csv.call_args[1]['columns'],
                         [self.tmap.data_options.weight_units] +
                         [str(x) for x in
                          range(1, self.tmap.display_options.depth + 1)])
