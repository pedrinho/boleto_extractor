#!/usr/bin/env python3
"""
End-to-end tests over real PDF files, with nothing mocked.

These are the tests that actually exercise rasterisation -> barcode decode ->
check digit validation -> linha digitavel conversion against known input, and
the text path for a linha printed on the page.

Fixtures are synthetic (see tests/fixtures/generate_fixtures.py) so no real payment
data is committed, but they are genuine Interleaved 2 of 5 symbols and are decoded
by the same code path a real boleto takes.
"""

import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from boleto_extractor import BoletoExtractor, PasswordRequired, WrongPassword

FIXTURES = Path(__file__).parent / 'fixtures'

# barcode payload -> expected linha digitavel (47 digits for bank boletos, 48 for
# arrecadacao/utility boletos).
# The Bradesco value is corroborated by the worked example in README.md
# ("19790.00005 04572.849356 62771.035649 7 11690000038600").
CASES = [
    (
        'boleto_bradesco.pdf',
        '19797116900000386000000004572849356277103564',
        '19790000050457284935662771035649711690000038600',
    ),
    (
        'boleto_bb.pdf',
        '00197234500000150000000123456789012345678901',
        '00190000172345678901723456789017723450000015000',
    ),
    (
        'boleto_itau.pdf',
        '34192098700002500001234567890123456789012345',
        '34191234546789012345767890123457209870000250000',
    ),
    (
        'boleto_arrecadacao.pdf',
        '82650000001234500011234567890123456789012345',
        '826500000011234500011239456789012345567890123456',
    ),
    (
        'boleto_text_only.pdf',
        '03391160000000123459123456700000123456780101',
        '03399123475670000012034567801013116000000012345',
    ),
]

ENCRYPTED = FIXTURES / 'boleto_encrypted.pdf'
TODAY = date(2026, 10, 23)


class TestEndToEndExtraction(unittest.TestCase):
    """Full pipeline, no mocks."""

    def setUp(self):
        self.extractor = BoletoExtractor()

    def test_fixtures_exist(self):
        """Guard against the fixtures being lost - the tests below would silently weaken."""
        for name in [case[0] for case in CASES] + [ENCRYPTED.name]:
            self.assertTrue(
                (FIXTURES / name).is_file(),
                f"Missing fixture {name}. Regenerate with "
                f"venv/bin/python tests/fixtures/generate_fixtures.py",
            )

    def test_full_extraction_returns_linha_digitavel(self):
        """The public entry point returns exactly the expected linha digitavel."""
        for name, _, expected in CASES:
            with self.subTest(fixture=name):
                self.assertEqual(self.extractor.extract_boleto_numbers(str(FIXTURES / name)), [expected])

    def test_barcode_is_decoded_from_pdf(self):
        """The raw 44-digit barcode is read back, from the barcode or the printed linha."""
        for name, barcode, _ in CASES:
            with self.subTest(fixture=name):
                found = self.extractor.extract(FIXTURES / name)
                self.assertEqual([b.barcode for b in found], [barcode])

    def test_conversion_matches_decoded_barcode(self):
        """Converting the decoded barcode directly agrees with the full pipeline."""
        for name, barcode, expected in CASES:
            with self.subTest(fixture=name):
                self.assertEqual(
                    self.extractor.barcode_to_linha_digitavel(barcode), expected
                )

    def test_bytes_and_paths_agree(self):
        for name, _, expected in CASES:
            with self.subTest(fixture=name):
                data = (FIXTURES / name).read_bytes()
                self.assertEqual(self.extractor.extract_boleto_numbers(data), [expected])

    def test_payment_details(self):
        bradesco, = self.extractor.extract(FIXTURES / 'boleto_bradesco.pdf', today=TODAY)
        self.assertEqual(bradesco.amount, Decimal('386.00'))
        self.assertEqual(bradesco.due_date, date(2025, 8, 10))

        utility, = self.extractor.extract(FIXTURES / 'boleto_arrecadacao.pdf', today=TODAY)
        self.assertEqual(utility.amount, Decimal('123.45'))
        self.assertEqual(utility.segment, 'Water and sanitation')

    def test_encrypted_pdf(self):
        with self.assertRaises(PasswordRequired):
            self.extractor.extract(ENCRYPTED)
        with self.assertRaises(WrongPassword):
            self.extractor.extract(ENCRYPTED, 'wrong')
        self.assertEqual(
            self.extractor.extract_boleto_numbers(str(ENCRYPTED), 'secret'),
            ['19790000050457284935662771035649711690000038600'],
        )

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.extractor.extract_boleto_numbers(str(FIXTURES / 'does_not_exist.pdf'))


if __name__ == '__main__':
    unittest.main()
