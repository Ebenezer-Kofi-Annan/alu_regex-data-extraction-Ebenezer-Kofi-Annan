"""Acceptance cases for the eight assignment categories and the command line."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

from regex_extractor import extract, validate


EXAMPLES = {
    "emails": ["user@example.com", "firstname.lastname@company.co.uk", "a+b@example.org"],
    "urls": [
        "https://www.example.com",
        "https://subdomain.example.org/page",
        "http://example.net:8080/docs/a%20b?q=one&sort=asc#section",
    ],
    "phones": ["(123) 456-7890", "123-456-7890", "123.456.7890", "123 456 7890"],
    "credit_cards": ["1234 5678 9012 3456", "1234-5678-9012-3456"],
    "times": ["14:30", "2:30 PM", "00:00", "23:59", "12:00 am"],
    "html_tags": [
        "<p>",
        '<div class="example">',
        '<img src="image.jpg" alt="description">',
        "</div>",
        "<br />",
        "<input disabled title='a > b'>",
    ],
    "hashtags": ["#example", "#ThisIsAHashtag", "#python_3", "#café"],
    "currencies": ["$19.99", "$1,234.56", "$0.00", "$1234.56"],
}

MALFORMED = {
    "emails": ["user..name@example.com", "user@-example.com", "user@example", "a@@b.co"],
    "urls": ["https://example", "https://-example.com", "https://example.com:abc", "https://example.com/a%zz"],
    "phones": ["(123 456-7890", "123-456.7890", "1123-456-7890", "123-456-78901"],
    "credit_cards": ["1234-5678 9012-3456", "1234 5678 9012 34567", "1234-5678-9012-3456-7890"],
    "times": ["24:00", "12:60", "00:30 AM", "13:30 PM", "11:30:00"],
    "html_tags": ["<123>", "</div class=x>", '<div class="open>', "<img src=>"],
    "hashtags": ["#", "##python", "C#example"],
    "currencies": ["$12,34.56", "$19.9", "$19.999", "-$19.99", "$19.99.10"],
}


class ExtractorTests(unittest.TestCase):
    def test_extracts_all_categories_from_mixed_text(self):
        text = "\n".join("; ".join(values) for values in EXAMPLES.values())
        self.assertEqual(extract(text), EXAMPLES)

    def test_preserves_order_and_repeated_matches(self):
        self.assertEqual(extract("#one #two #one")["hashtags"], ["#one", "#two", "#one"])

    def test_excludes_prose_punctuation_from_urls(self):
        text = 'Visit (https://example.org/docs), then "https://example.com/help?x=1".'
        self.assertEqual(
            extract(text)["urls"],
            ["https://example.org/docs", "https://example.com/help?x=1"],
        )
        self.assertEqual(extract("Visit https://example.org/docs.")["urls"], ["https://example.org/docs"])

    def test_reports_empty_lists_for_missing_categories(self):
        self.assertEqual(extract("Nothing here."), {category: [] for category in EXAMPLES})

    def test_validates_every_supported_example(self):
        for category, values in EXAMPLES.items():
            for value in values:
                with self.subTest(category=category, value=value):
                    self.assertTrue(validate(category, value))

    def test_validation_requires_a_whole_value(self):
        self.assertFalse(validate("emails", "Email user@example.com for help"))
        self.assertFalse(validate("emails", "user@example.com."))
        self.assertFalse(validate("emails", " user@example.com "))

    def test_rejects_malformed_values_and_partial_matches(self):
        for category, values in MALFORMED.items():
            for value in values:
                with self.subTest(category=category, value=value):
                    self.assertFalse(validate(category, value))
                    self.assertEqual(extract(f"Before ({value}), after.")[category], [])


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *args, text=None):
        script = Path(__file__).resolve().parents[1] / "regex_extractor.py"
        return subprocess.run(
            [sys.executable, str(script), *args],
            input=text,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_extract_reads_standard_input_and_prints_json(self):
        result = self.run_cli("extract", text="Contact user@example.com at 14:30.")
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = {category: [] for category in EXAMPLES}
        expected["emails"] = ["user@example.com"]
        expected["times"] = ["14:30"]
        self.assertEqual(json.loads(result.stdout), expected)

    def test_validate_exit_codes_distinguish_valid_and_invalid_values(self):
        valid = self.run_cli("validate", "times", "2:30 PM")
        invalid = self.run_cli("validate", "times", "24:00")
        self.assertEqual((valid.returncode, valid.stdout.strip()), (0, "Valid"))
        self.assertEqual((invalid.returncode, invalid.stdout.strip()), (1, "Invalid"))

    def test_extract_reports_missing_file_as_usage_error(self):
        result = self.run_cli("extract", "__missing_regex_extractor_input__.txt")
        self.assertEqual(result.returncode, 2)
        self.assertIn("__missing_regex_extractor_input__.txt", result.stderr)


if __name__ == "__main__":
    unittest.main()
