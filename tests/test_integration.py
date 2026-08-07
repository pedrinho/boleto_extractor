#!/usr/bin/env python3
"""
End-to-end tests over real PDF files, with nothing mocked.

The rest of the suite mocks the barcode decoder, which means it stays green even if
decoding is completely broken. These tests are the ones that actually exercise
rasterisation -> barcode decode -> linha digitavel conversion against known input.

Fixtures are synthetic (see tests/fixtures/generate_fixtures.py) so no real payment
data is committed, but they are genuine Interleaved 2 of 5 symbols and are decoded
by the same code path a real boleto takes.
"""

import unittest
from pathlib import Path

from boleto_extractor.extractor import BoletoExtractor

FIXTURES = Path(__file__).parent / 'fixtures'

# barcode payload -> expected 47-digit linha digitavel.
# The Bradesco value is corroborated by the worked example in README.md
# ("19790.00005 04572.84935 66277.10356 4 9711690000038600").
CASES = [
    (
        'boleto_bradesco.pdf',
        '19797116900000386000000004572849356277103564',
        '19790000050457284935662771035649711690000038600',
    ),
    (
        'boleto_bb.pdf',
        '00191234500000150000000123456789012345678901',
        '00190000172345678901723456789017123450000015000',
    ),
    (
        'boleto_itau.pdf',
        '34191098700002500001234567890123456789012345',
        '34191234546789012345767890123457109870000250000',
    ),
]


class TestEndToEndExtraction(unittest.TestCase):
    """Full pipeline, no mocks."""

    def setUp(self):
        self.extractor = BoletoExtractor()

    def test_fixtures_exist(self):
        """Guard against the fixtures being lost - the tests below would silently weaken."""
        for name, _, _ in CASES:
            self.assertTrue(
                (FIXTURES / name).is_file(),
                f"Missing fixture {name}. Regenerate with "
                f"venv/bin/python tests/fixtures/generate_fixtures.py",
            )

    def test_barcode_is_decoded_from_pdf(self):
        """The raw 44-digit barcode is read back off the rendered page."""
        for name, barcode, _ in CASES:
            with self.subTest(fixture=name):
                found = self.extractor.scan_barcodes_in_pdf(str(FIXTURES / name))
                self.assertIn(barcode, found)

    def test_full_extraction_returns_linha_digitavel(self):
        """The public entry point returns the expected 47-digit number."""
        for name, _, expected in CASES:
            with self.subTest(fixture=name):
                results = self.extractor.extract_boleto_numbers(str(FIXTURES / name))
                self.assertIn(expected, results)
                for number in results:
                    self.assertEqual(len(number), 47)
                    self.assertTrue(number.isdigit())

    def test_conversion_matches_decoded_barcode(self):
        """Converting the decoded barcode directly agrees with the full pipeline."""
        for name, barcode, expected in CASES:
            with self.subTest(fixture=name):
                self.assertEqual(
                    self.extractor.barcode_to_linha_digitavel(barcode), expected
                )

    def test_missing_file_returns_empty(self):
        """A path that does not exist yields no results rather than raising."""
        self.assertEqual(
            self.extractor.extract_boleto_numbers(str(FIXTURES / 'does_not_exist.pdf')), []
        )


if __name__ == '__main__':
    unittest.main()
