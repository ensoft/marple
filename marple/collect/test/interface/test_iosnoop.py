# -------------------------------------------------------------
# test_iosnoop.py - tests for interaction with iosnoop
# August 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

""" Test iosnoop interactions. """

import asynctest

from marple.collect.interface import iosnoop
from marple.common import data_io


class DiskLatencyTest(asynctest.TestCase):
    """ Test disk latency data collection. """
    time = 5
    async_mock, log_mock, pipe_mock = None, None, None

    def run(self, result=None):
        """ Override run() to set up mocks """
        with asynctest.patch('marple.collect.interface.iosnoop.asyncio') as \
                async_mock, \
                asynctest.patch('marple.collect.interface.iosnoop.logger') as log_mock:
            self.async_mock = async_mock

            # Mock subprocess creator
            create_mock = asynctest.CoroutineMock()
            async_mock.create_subprocess_exec = create_mock

            # Mock communicate()
            comm_mock = asynctest.CoroutineMock()
            comm_mock.side_effect = [(b'\n\nA 1.0 B test_info D E F G 2.0',
                                      b'test_err')]
            create_mock.return_value.communicate = comm_mock

            self.log_mock = log_mock
            self.pipe_mock = async_mock.subprocess.PIPE

            # Call super
            super().run(result)

    async def test(self):
        collecter = iosnoop.DiskLatency(self.time, None)
        data = await collecter.collect()
        datapoints = list(data.datum_generator)

        self.async_mock.create_subprocess_exec.assert_has_calls([
            asynctest.call(
                iosnoop.IOSNOOP_SCRIPT, '-ts', str(self.time),
                stdout=self.pipe_mock, stderr=self.pipe_mock),
            asynctest.call().communicate()
        ])

        self.log_mock.error.assert_called_once_with('test_err')

        expected = [data_io.PointDatum(x=1.0, y=2.0, info='test_info')]
        self.assertEqual(expected, datapoints)
