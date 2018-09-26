# --------------------------------------------------------------------
# test_main.py - test the controller for the collect module.
# June - September 2018 - Franz Nowak, Hrutvik Kanabar, Andrei Diaconu
# --------------------------------------------------------------------


import unittest
from unittest import mock

from marple.collect import main as collect
from marple.common import consts


class _ParseTest(unittest.TestCase):
    """Class for testing that parsing works correctly"""
    @mock.patch("marple.collect.main.config.get_section")
    def test_parse(self, get_opt_mock):
        get_opt_mock.side_effect = [{'ali': 'disklat,mallocstacks'}]
        args = collect._args_parse(['cpusched', 'memtime', 'ali', '-t', '10'])
        self.assertEqual(args.outfile, None)
        self.assertEqual(args.time, 10)
        self.assertListEqual(sorted(args.subcommands), sorted(['cpusched',
                                                               'memtime',
                                                               'ali']))


class MainTest(unittest.TestCase):
    """Class that tests the main function calls are correct"""

    @mock.patch('marple.common.data_io.Writer')
    @mock.patch('marple.collect.test.test_main.collect.config')
    @mock.patch('marple.collect.test.test_main.collect.output')
    @mock.patch('marple.collect.test.test_main.collect.file')
    @mock.patch('marple.collect.test.test_main.collect._get_collecters')
    @mock.patch('marple.collect.test.test_main.collect._collect_results')
    def test_main(self, collect_mock, getc_mock, file_mock, outpt_mock,
                  config_mock, writer_mock):
        command = ['cpusched', 'memtime', '-o', 'out', '-t', '10']
        collect.main(command)

        file_mock.DataFileName.assert_called_once_with(given_name='out')
        file_mock.DataFileName().export_filename.assert_called_once()
        getc_mock.assert_called_once_with(['cpusched', 'memtime'], 10)
        collect_mock.assert_called_once()


class HelperFunctionsTest(unittest.TestCase):
    """Class that tests all the helper functions in the main module"""
    @mock.patch("marple.collect.test.test_main.collect._get_collecter_instance")
    @mock.patch("marple.collect.main.config.get_option_from_section")
    @mock.patch("marple.collect.main.config.configparser.ConfigParser.has_option")
    def test_get_collecters(self, has_opt, get_opt_mock, coll_inst_mock):
        # We patch the function from within the test module since it's here we
        # call it
        coll_inst_mock.side_effect = lambda com, time: com
        has_opt.side_effect = [True, False]
        get_opt_mock.side_effect = ['disklat,mallocstacks']

        answ = collect._get_collecters(['cpusched', 'memtime', 'alias'], 10)
        self.assertListEqual(sorted(answ), sorted(['cpusched', 'memtime',
                                                   'disklat', 'mallocstacks']))

        with self.assertRaises(ValueError):
            collect._get_collecters(['INVALID'], 10)

    @mock.patch("marple.collect.main.config.get_option_from_section")
    @mock.patch("marple.collect.test.test_main.collect.perf")
    @mock.patch("marple.collect.test.test_main.collect.ebpf")
    @mock.patch("marple.collect.test.test_main.collect.iosnoop")
    @mock.patch("marple.collect.test.test_main.collect.smem")
    def test_get_collecter_instance(self, smem_mock, iosnoop_mock,
                                    ebpf_mock, perf_mock, get_opt_mock):

        inter_to_mock = {
            'cpusched': perf_mock.SchedulingEvents,
            'disklat': iosnoop_mock.DiskLatency,
            'mallocstacks': ebpf_mock.MallocStacks,
            'memusage': ebpf_mock.Memleak,
            'memtime': smem_mock.MemoryGraph,
            'callstack': perf_mock.StackTrace,
            'ipc': ebpf_mock.TCPTracer,
            'memevents': perf_mock.MemoryEvents,
            'diskblockrq': perf_mock.DiskBlockRequests,
            'perf_malloc': perf_mock.MemoryMalloc,
        }

        for cmd in consts.interfaces_argnames:
            collect._get_collecter_instance(cmd, 10)
            inter_to_mock[cmd].assert_called()
