import importlib
import sys
import unittest


class PackageImportTests(unittest.TestCase):
    def test_import_runstats_does_not_eagerly_import_cli(self) -> None:
        sys.modules.pop("runstats", None)
        sys.modules.pop("runstats.cli", None)

        package = importlib.import_module("runstats")

        self.assertTrue(callable(package.main))
        self.assertNotIn("runstats.cli", sys.modules)
