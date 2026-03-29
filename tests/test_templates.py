import unittest

from runstats.templates import TEMPLATE_NAMES


class TemplateRegistryTests(unittest.TestCase):
    def test_stitch_story_template_is_registered(self) -> None:
        self.assertIn("neon_data_story", TEMPLATE_NAMES)


if __name__ == "__main__":
    unittest.main()
