import collect.test.util as util

# -----------------------------------------------------------------------------
# Helpers
#


class _BaseTest(util.BaseTest):
    """Base test class for perf testing."""
    pass

class _ParseTest(_BaseTest):
    """Class for testing that parsing works correctly"""

class ParserTest(_BaseTest):
    def test_parse(self):
        pass