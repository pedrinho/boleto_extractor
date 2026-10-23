#!/usr/bin/env python3
"""
Tests for the pure barcode and linha digitável rules in boleto_extractor.barcode.

The Bradesco number is the worked example from README.md; the others match the
synthetic PDF fixtures (see tests/fixtures/generate_fixtures.py).
"""

import unittest
from datetime import date
from decimal import Decimal

from boleto_extractor.barcode import (
    BoletoInfo,
    barcode_to_linha,
    decode,
    find_barcodes_in_text,
    format_brl,
    format_linha,
    is_valid_barcode,
    linha_to_barcode,
    mod10,
    mod11,
    mod11_bank,
)

BRADESCO_BARCODE = '19797116900000386000000004572849356277103564'
BRADESCO_LINHA = '19790000050457284935662771035649711690000038600'
BRADESCO_PRINTED = '19790.00005 04572.849356 62771.035649 7 11690000038600'

ARRECADACAO_BARCODE = '82650000001234500011234567890123456789012345'
ARRECADACAO_LINHA = '826500000011234500011239456789012345567890123456'
ARRECADACAO_PRINTED = '82650000001-1 23450001123-9 45678901234-5 56789012345-6'

SANTANDER_BARCODE = '03391160000000123459123456700000123456780101'
SANTANDER_PRINTED = '03399.12347 56700.000120 34567.801013 1 16000000012345'

TODAY = date(2026, 10, 23)


def with_arrecadacao_dv(barcode):
    """Fill in the general check digit (position 4) of an arrecadação barcode."""
    body = barcode[:3] + barcode[4:]
    check = mod10 if barcode[2] in '67' else mod11
    return barcode[:3] + str(check(body)) + barcode[4:]


def with_bank_dv(barcode):
    """Fill in the general check digit (position 5) of a bank barcode."""
    return barcode[:4] + str(mod11_bank(barcode[:4] + barcode[5:])) + barcode[5:]


class TestCheckDigits(unittest.TestCase):

    def test_mod10_matches_printed_field_check_digits(self):
        # Each field of the printed linha ends in its own modulo 10 digit.
        self.assertEqual(mod10('197900000'), 5)
        self.assertEqual(mod10('0457284935'), 6)
        self.assertEqual(mod10('6277103564'), 9)

    def test_mod11_bank_maps_0_10_11_to_1(self):
        self.assertEqual(mod11_bank('0' * 43), 1)  # 11 - 0 = 11 -> 1

    def test_mod11_maps_remainders_0_and_1_to_0(self):
        self.assertEqual(mod11('0' * 43), 0)

    def test_valid_barcodes(self):
        for barcode in (BRADESCO_BARCODE, ARRECADACAO_BARCODE, SANTANDER_BARCODE):
            with self.subTest(barcode=barcode):
                self.assertTrue(is_valid_barcode(barcode))

    def test_wrong_general_check_digit_is_rejected(self):
        self.assertFalse(is_valid_barcode(BRADESCO_BARCODE[:4] + '1' + BRADESCO_BARCODE[5:]))
        self.assertFalse(is_valid_barcode(ARRECADACAO_BARCODE[:3] + '0' + ARRECADACAO_BARCODE[4:]))

    def test_changed_payload_digit_is_rejected(self):
        tampered = BRADESCO_BARCODE[:20] + '9' + BRADESCO_BARCODE[21:]
        self.assertNotEqual(tampered, BRADESCO_BARCODE)
        self.assertFalse(is_valid_barcode(tampered))

    def test_malformed_input_is_rejected(self):
        for value in (None, '', '123', BRADESCO_BARCODE + '0', BRADESCO_BARCODE[:-1],
                      BRADESCO_BARCODE[:-1] + 'a', BRADESCO_BARCODE[:-1] + '١', 12345):
            with self.subTest(value=value):
                self.assertFalse(is_valid_barcode(value))

    def test_arrecadacao_with_unknown_value_identifier_is_rejected(self):
        self.assertFalse(is_valid_barcode('825' + ARRECADACAO_BARCODE[3:]))


class TestConversion(unittest.TestCase):

    def test_barcode_to_linha(self):
        self.assertEqual(barcode_to_linha(BRADESCO_BARCODE), BRADESCO_LINHA)
        self.assertEqual(barcode_to_linha(ARRECADACAO_BARCODE), ARRECADACAO_LINHA)

    def test_barcode_to_linha_rejects_bad_input(self):
        for value in (None, '', '123', BRADESCO_BARCODE + '0', 'a' * 44, '825' + ARRECADACAO_BARCODE[3:]):
            with self.subTest(value=value):
                self.assertIsNone(barcode_to_linha(value))

    def test_arrecadacao_mod11_blocks(self):
        barcode = with_arrecadacao_dv('8380' + ARRECADACAO_BARCODE[4:])
        linha = barcode_to_linha(barcode)
        self.assertEqual(len(linha), 48)
        for i in range(0, 48, 12):
            self.assertEqual(int(linha[i + 11]), mod11(linha[i:i + 11]))

    def test_round_trip(self):
        for barcode in (BRADESCO_BARCODE, ARRECADACAO_BARCODE, SANTANDER_BARCODE):
            with self.subTest(barcode=barcode):
                self.assertEqual(linha_to_barcode(barcode_to_linha(barcode)), barcode)

    def test_linha_with_bad_field_check_digit_is_rejected(self):
        for position in (9, 20, 31):
            with self.subTest(position=position):
                digit = str((int(BRADESCO_LINHA[position]) + 1) % 10)
                bad = BRADESCO_LINHA[:position] + digit + BRADESCO_LINHA[position + 1:]
                self.assertIsNone(linha_to_barcode(bad))

    def test_linha_with_bad_general_check_digit_is_rejected(self):
        bad = BRADESCO_LINHA[:32] + '1' + BRADESCO_LINHA[33:]
        self.assertIsNone(linha_to_barcode(bad))

    def test_arrecadacao_linha_with_bad_block_check_digit_is_rejected(self):
        bad = ARRECADACAO_LINHA[:11] + '0' + ARRECADACAO_LINHA[12:]
        self.assertIsNone(linha_to_barcode(bad))

    def test_linha_to_barcode_rejects_malformed_input(self):
        for value in (None, '', BRADESCO_LINHA[:-1], '1' + ARRECADACAO_LINHA[1:], BRADESCO_PRINTED):
            with self.subTest(value=value):
                self.assertIsNone(linha_to_barcode(value))


class TestFormatting(unittest.TestCase):

    def test_bank_linha_is_grouped_as_printed(self):
        self.assertEqual(format_linha(BRADESCO_LINHA), BRADESCO_PRINTED)

    def test_arrecadacao_linha_is_grouped_as_printed(self):
        self.assertEqual(format_linha(ARRECADACAO_LINHA), ARRECADACAO_PRINTED)

    def test_formatting_keeps_every_digit_in_order(self):
        self.assertEqual(format_linha(BRADESCO_LINHA).replace('.', '').replace(' ', ''), BRADESCO_LINHA)

    def test_other_lengths_are_unchanged(self):
        for value in ('', None, '123', BRADESCO_BARCODE):
            with self.subTest(value=value):
                self.assertEqual(format_linha(value), value)

    def test_format_brl(self):
        self.assertEqual(format_brl(Decimal('386.00')), 'R$ 386,00')
        self.assertEqual(format_brl(Decimal('1234567.8')), 'R$ 1.234.567,80')
        self.assertEqual(format_brl(Decimal('0.5')), 'R$ 0,50')


class TestTextSearch(unittest.TestCase):

    def test_printed_bank_linha(self):
        text = f"Banco Bradesco | 237-2 | {BRADESCO_PRINTED}\nLocal de pagamento"
        self.assertEqual(find_barcodes_in_text(text), [BRADESCO_BARCODE])

    def test_unformatted_and_space_separated_bank_linha(self):
        spaced = BRADESCO_PRINTED.replace('.', ' ')
        for text in (BRADESCO_LINHA, spaced, f"linha:{BRADESCO_LINHA}."):
            with self.subTest(text=text):
                self.assertEqual(find_barcodes_in_text(text), [BRADESCO_BARCODE])

    def test_printed_arrecadacao_linha(self):
        for text in (ARRECADACAO_PRINTED, ARRECADACAO_PRINTED.replace('-', ' '), ARRECADACAO_LINHA):
            with self.subTest(text=text):
                self.assertEqual(find_barcodes_in_text(text), [ARRECADACAO_BARCODE])

    def test_bad_check_digit_is_ignored(self):
        bad = BRADESCO_PRINTED[:10] + '6' + BRADESCO_PRINTED[11:]
        self.assertEqual(find_barcodes_in_text(bad), [])

    def test_bare_44_digit_run_is_ignored(self):
        # An NF-e access key is 44 digits too, and would pass the single check
        # digit about one time in eleven.
        self.assertEqual(find_barcodes_in_text(f"Chave de acesso: {BRADESCO_BARCODE}"), [])

    def test_linha_inside_a_longer_digit_run_is_ignored(self):
        self.assertEqual(find_barcodes_in_text('1' + BRADESCO_LINHA), [])
        self.assertEqual(find_barcodes_in_text(BRADESCO_LINHA + '1'), [])

    def test_several_boletos_in_order_without_duplicates(self):
        text = f"{SANTANDER_PRINTED}\n{BRADESCO_PRINTED}\nRecibo: {SANTANDER_PRINTED}"
        self.assertEqual(find_barcodes_in_text(text), [SANTANDER_BARCODE, BRADESCO_BARCODE])

    def test_two_linhas_separated_by_a_space(self):
        text = f"{BRADESCO_LINHA} {barcode_to_linha(SANTANDER_BARCODE)}"
        self.assertEqual(find_barcodes_in_text(text), [BRADESCO_BARCODE, SANTANDER_BARCODE])

    def test_empty_text(self):
        self.assertEqual(find_barcodes_in_text(''), [])
        self.assertEqual(find_barcodes_in_text(None), [])


class TestDecode(unittest.TestCase):

    def test_bank_boleto(self):
        info = decode(BRADESCO_BARCODE, today=TODAY)
        self.assertEqual(info.kind, 'bank')
        self.assertEqual(info.linha, BRADESCO_LINHA)
        self.assertEqual(info.formatted, BRADESCO_PRINTED)
        self.assertEqual(info.amount, Decimal('386.00'))
        self.assertEqual(info.due_date, date(2025, 8, 10))  # factor 1169, second cycle
        self.assertIsNone(info.segment)

    def test_due_date_factor_resolves_to_the_nearer_cycle(self):
        # Factor 1169 is 2000-12-19 in the first cycle and 2025-08-10 in the second.
        self.assertEqual(decode(BRADESCO_BARCODE, today=date(2001, 1, 1)).due_date, date(2000, 12, 19))
        self.assertEqual(decode(BRADESCO_BARCODE, today=date(2025, 1, 1)).due_date, date(2025, 8, 10))

    def test_due_date_factor_rollover(self):
        last = with_bank_dv('23790' + '9999' + BRADESCO_BARCODE[9:])
        first = with_bank_dv('23790' + '1000' + BRADESCO_BARCODE[9:])
        self.assertEqual(decode(last, today=date(2025, 2, 1)).due_date, date(2025, 2, 21))
        self.assertEqual(decode(first, today=date(2025, 2, 1)).due_date, date(2025, 2, 22))

    def test_zero_factor_and_amount_mean_not_specified(self):
        info = decode(with_bank_dv('23790' + '0000' + '0000000000' + BRADESCO_BARCODE[19:]), today=TODAY)
        self.assertIsNone(info.due_date)
        self.assertIsNone(info.amount)

    def test_arrecadacao_with_amount_in_reais(self):
        info = decode(ARRECADACAO_BARCODE, today=TODAY)
        self.assertEqual(info.kind, 'arrecadacao')
        self.assertEqual(info.amount, Decimal('123.45'))
        self.assertIsNone(info.due_date)
        self.assertEqual(info.segment, 'Water and sanitation')
        self.assertEqual(info.kind_label, 'Utility/tax bill')

    def test_arrecadacao_with_reference_value_has_no_amount(self):
        for value_id in '79':
            with self.subTest(value_id=value_id):
                barcode = with_arrecadacao_dv('83' + value_id + '0' + ARRECADACAO_BARCODE[4:])
                info = decode(barcode, today=TODAY)
                self.assertIsNone(info.amount)
                self.assertEqual(info.segment, 'Electricity and gas')

    def test_invalid_barcode_raises(self):
        with self.assertRaises(ValueError):
            decode(BRADESCO_BARCODE[:4] + '1' + BRADESCO_BARCODE[5:])

    def test_as_dict(self):
        self.assertEqual(decode(BRADESCO_BARCODE, today=TODAY).as_dict(), {
            'barcode': BRADESCO_BARCODE,
            'linha': BRADESCO_LINHA,
            'formatted': BRADESCO_PRINTED,
            'kind': 'bank',
            'amount': '386.00',
            'due_date': '2025-08-10',
            'segment': None,
        })

    def test_info_is_immutable(self):
        info = decode(BRADESCO_BARCODE, today=TODAY)
        self.assertIsInstance(info, BoletoInfo)
        with self.assertRaises(AttributeError):
            info.amount = Decimal('1')


if __name__ == '__main__':
    unittest.main()
