# -------------------------------------------------------------
# test_main.py - test the controller for the collect module.
# June - August 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

# TODO add tests once collect UI has been updated

# import unittest
# from unittest import mock
#
# import collect.controller.main as collect
#
#
# class _ParseTest(unittest.TestCase):
#     """Class for testing that parsing works correctly"""
#     @staticmethod
#     def check_calls(argv, cls, fn, args, **kwargs):
#         """
#         Stubs out a given function and checks that it gets called
#         after correctly passing the input.
#
#         :param argv:
#             The arguments passed to the main function.
#         :param cls:
#             The class or module from which to take the function.
#         :param fn:
#             The function that should be stubbed out and get called.
#         :param args:
#             The arguments to the function that was stubbed out.
#         :param kwargs:
#             The keyword arguments to the function that was stubbed out.
#         """
#         with mock.patch.object(cls, fn) as call_mock:
#             collect.main(argv)
#             call_mock.assert_called_once_with(*args, **kwargs)
