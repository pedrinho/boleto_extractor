#!/usr/bin/env python3
"""
Unit tests for the BoletoExtractor facade.

The barcode rules and the PDF layer have their own tests (test_barcode.py,
test_pdf.py); these cover how the extractor combines them. Only the barcode
decoder is ever mocked, and only to control what it reports.
"""

import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pymupdf

from boleto_extractor import (
    BoletoExtractor,
    PasswordRequired,
    extract_boleto_numbers,
    find_boleto_numbers_in_text,
    is_valid_boleto_number,
)

FIXTURES = Path(__file__).parent / 'fixtures'

BRADESCO_BARCODE = '19797116900000386000000004572849356277103564'
BRADESCO_LINHA = '19790000050457284935662771035649711690000038600'
BRADESCO_PRINTED = '19790.00005 04572.849356 62771.035649 7 11690000038600'
SANTANDER_LINHA = '03399123475670000012034567801013116000000012345'


def text_pdf(*lines):
    doc = pymupdf.open()
    page = doc.new_page()
    for i, line in enumerate(lines):
        page.insert_text((50, 50 + 20 * i), line)
    data = doc.tobytes()
    doc.close()
    return data


def zxing_results(*texts):
    return [SimpleNamespace(text=t) for t in texts]


class TestExtract(unittest.TestCase):

    def setUp(self):
        self.extractor = BoletoExtractor()

    def test_reads_printed_linha_without_rendering(self):
        with patch('boleto_extractor.extractor.zxingcpp.read_barcodes') as read:
            boletos = self.extractor.extract(text_pdf('Linha digitavel:', BRADESCO_PRINTED))
        read.assert_not_called()
        self.assertEqual([b.linha for b in boletos], [BRADESCO_LINHA])

    def test_falls_back_to_barcode_when_text_has_no_linha(self):
        with patch('boleto_extractor.extractor.zxingcpp.read_barcodes',
                   return_value=zxing_results(BRADESCO_BARCODE)) as read:
            boletos = self.extractor.extract(text_pdf('No numbers here'))
        read.assert_called_once()
        self.assertEqual([b.barcode for b in boletos], [BRADESCO_BARCODE])

    def test_barcode_reads_with_bad_check_digit_are_dropped(self):
        misread = BRADESCO_BARCODE[:4] + '1' + BRADESCO_BARCODE[5:]
        with patch('boleto_extractor.extractor.zxingcpp.read_barcodes',
                   return_value=zxing_results(misread, '12345', BRADESCO_BARCODE)):
            boletos = self.extractor.extract(text_pdf('x'))
        self.assertEqual([b.barcode for b in boletos], [BRADESCO_BARCODE])

    def test_duplicates_are_collapsed_in_order(self):
        pdf = text_pdf(SANTANDER_LINHA, BRADESCO_PRINTED, SANTANDER_LINHA)
        self.assertEqual(self.extractor.extract_boleto_numbers(pdf), [SANTANDER_LINHA, BRADESCO_LINHA])

    def test_today_is_passed_to_decode(self):
        boleto, = self.extractor.extract(text_pdf(BRADESCO_PRINTED), today=date(2001, 1, 1))
        self.assertEqual(boleto.due_date, date(2000, 12, 19))

    def test_nothing_found(self):
        self.assertEqual(self.extractor.extract(text_pdf('Nada aqui')), [])

    def test_errors_propagate(self):
        with self.assertRaises(PasswordRequired):
            self.extractor.extract(FIXTURES / 'boleto_encrypted.pdf')
        with self.assertRaises(FileNotFoundError):
            self.extractor.extract_boleto_numbers(str(FIXTURES / 'does_not_exist.pdf'))


class TestCompatibilityApi(unittest.TestCase):
    """The methods and functions documented in README.md."""

    def setUp(self):
        self.extractor = BoletoExtractor()

    def test_methods(self):
        self.assertEqual(self.extractor.barcode_to_linha_digitavel(BRADESCO_BARCODE), BRADESCO_LINHA)
        self.assertEqual(self.extractor.format_boleto_number(BRADESCO_LINHA), BRADESCO_PRINTED)
        self.assertTrue(self.extractor.is_valid_boleto_number(BRADESCO_BARCODE))
        self.assertEqual(self.extractor.find_boleto_numbers_in_text(BRADESCO_PRINTED), [BRADESCO_BARCODE])

    def test_module_functions(self):
        pdf = str(FIXTURES / 'boleto_bradesco.pdf')
        self.assertEqual(extract_boleto_numbers(pdf), [BRADESCO_LINHA])
        self.assertEqual(find_boleto_numbers_in_text(BRADESCO_PRINTED), [BRADESCO_BARCODE])
        self.assertTrue(is_valid_boleto_number(BRADESCO_BARCODE))
        self.assertFalse(is_valid_boleto_number('1' * 44))


if __name__ == '__main__':
    unittest.main()
