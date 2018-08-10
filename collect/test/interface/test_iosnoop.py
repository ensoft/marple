import unittest
from unittest import mock

from collect.interface import iosnoop
from common import datatypes


class _IosnoopCollecterBaseTest(unittest.TestCase):
    # Override run to apply patches for all tests
    time = 5

    def run(self, result=None):
        with mock.patch('collect.interface.iosnoop.subprocess') as \
                subproc_mock, \
                mock.patch('collect.interface.iosnoop.logger') as log_mock:
            self.subproc_mock = subproc_mock
            self.log_mock = log_mock
            self.subproc_mock.Popen.return_value.communicate.side_effect = \
                [(b'\n\nA 1.0 B test_info D E F G 2.0',
                  b"test_err")]
            self.pipe_mock = self.subproc_mock.PIPE
            super().run(result)


class DiskLatencyTest(_IosnoopCollecterBaseTest):

    @mock.patch('collect.interface.perf.StackParser')
    def test(self, stack_parse_mock):

        collecter = iosnoop.DiskLatency(self.time, None)
        datapoints = list(collecter.collect())

        expected_calls = [
            mock.call([iosnoop.IOSNOOP_SCRIPT, '-ts', str(self.time)],
                      stdout=self.pipe_mock, stderr=self.pipe_mock),
            mock.call().communicate()
        ]

        self.subproc_mock.Popen.assert_has_calls(expected_calls)

        expected_logs = [
            mock.call("test_err"),
        ]
        self.log_mock.error.assert_has_calls(expected_logs)

        expected = [datatypes.Datapoint(x=1.0, y=2.0, info='test_info')]

        self.assertEqual(expected, datapoints)