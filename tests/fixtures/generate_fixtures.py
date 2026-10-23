#!/usr/bin/env python3
"""
Regenerate the boleto PDF fixtures used by tests/test_integration.py.

Real boletos carry payment data, so the fixtures are synthetic: most render a
known 44-digit payload as a genuine Interleaved 2 of 5 barcode (the symbology
Brazilian boletos use) into a PDF. Because the payload is known up front, the tests
can assert an exact expected result rather than whatever the decoder happens to say.

Two cover the other paths: one prints only the linha digitável as text, with no
barcode, and one is encrypted with the user password "secret".

Usage:
    venv/bin/python tests/fixtures/generate_fixtures.py
"""

import sys
from pathlib import Path

import pymupdf

# Interleaved 2 of 5: each digit is five elements, two wide (W) and three narrow (N).
ITF_PATTERNS = {
    '0': 'NNWWN',
    '1': 'WNNNW',
    '2': 'NWNNW',
    '3': 'WWNNN',
    '4': 'NNWNW',
    '5': 'WNWNN',
    '6': 'NWWNN',
    '7': 'NNNWW',
    '8': 'WNNWN',
    '9': 'NWNWN',
}

NARROW = 2.0        # points
WIDE_RATIO = 3.0    # ITF permits 2:1 to 3:1; 3:1 decodes most reliably
BAR_HEIGHT = 60.0
MARGIN = 40.0

# The payloads under test. Each is a 44-digit barcode with a correct general check
# digit, as on a real boleto - the extractor rejects any other. The first is the
# one the README example uses, so its expected output is independently known.
# The arrecadação one is a utility bill (starts with 8).
FIXTURES = {
    'boleto_bradesco.pdf':    '19797116900000386000000004572849356277103564',
    'boleto_bb.pdf':          '00197234500000150000000123456789012345678901',
    'boleto_itau.pdf':        '34192098700002500001234567890123456789012345',
    'boleto_arrecadacao.pdf': '82650000001234500011234567890123456789012345',
}

# Printed as text only: the linha digitável of a Santander boleto.
TEXT_ONLY_FIXTURE = 'boleto_text_only.pdf'
TEXT_ONLY_LINHA = '03399.12347 56700.000120 34567.801013 1 16000000012345'

# The Bradesco barcode again, in a PDF that needs a password to open.
ENCRYPTED_FIXTURE = 'boleto_encrypted.pdf'
ENCRYPTED_PAYLOAD = FIXTURES['boleto_bradesco.pdf']
ENCRYPTED_PASSWORD = 'secret'


def _elements(payload: str):
    """Yield (width_in_points, is_bar) for the full ITF symbol."""
    if len(payload) % 2 != 0:
        raise ValueError(f"ITF requires an even digit count, got {len(payload)}")

    wide = NARROW * WIDE_RATIO

    # Start pattern: narrow bar, narrow space, narrow bar, narrow space.
    for i in range(4):
        yield NARROW, i % 2 == 0

    # Digits are encoded in pairs: the first digit drives the bars, the second the
    # spaces, interleaved element by element.
    for i in range(0, len(payload), 2):
        bars = ITF_PATTERNS[payload[i]]
        spaces = ITF_PATTERNS[payload[i + 1]]
        for b, s in zip(bars, spaces):
            yield (wide if b == 'W' else NARROW), True
            yield (wide if s == 'W' else NARROW), False

    # Stop pattern: wide bar, narrow space, narrow bar.
    yield wide, True
    yield NARROW, False
    yield NARROW, True


def write_fixture(path: Path, payload: str, user_password: str = None) -> None:
    elements = list(_elements(payload))
    symbol_width = sum(width for width, _ in elements)

    doc = pymupdf.open()
    page = doc.new_page(
        width=symbol_width + 2 * MARGIN,
        height=BAR_HEIGHT + 2 * MARGIN + 40,
    )

    # A little context text, so the fixture also exercises the text-extraction path.
    page.insert_text((MARGIN, MARGIN - 12), "Boleto de teste - fixture sintetica", fontsize=10)

    x = MARGIN
    for width, is_bar in elements:
        if is_bar:
            rect = pymupdf.Rect(x, MARGIN, x + width, MARGIN + BAR_HEIGHT)
            page.draw_rect(rect, color=None, fill=(0, 0, 0))
        x += width

    if user_password:
        doc.save(str(path), encryption=pymupdf.PDF_ENCRYPT_AES_256,
                 user_pw=user_password, owner_pw=user_password + '-owner')
    else:
        doc.save(str(path))
    doc.close()


def write_text_fixture(path: Path, linha: str) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=200)
    page.insert_text((MARGIN, MARGIN), "Boleto de teste - fixture sintetica", fontsize=10)
    page.insert_text((MARGIN, MARGIN + 30), "Linha digitavel:", fontsize=10)
    page.insert_text((MARGIN, MARGIN + 50), linha, fontsize=12)
    doc.save(str(path))
    doc.close()


def main() -> int:
    here = Path(__file__).parent
    for name, payload in FIXTURES.items():
        write_fixture(here / name, payload)
        print(f"wrote {name}  ({payload})")
    write_text_fixture(here / TEXT_ONLY_FIXTURE, TEXT_ONLY_LINHA)
    print(f"wrote {TEXT_ONLY_FIXTURE}  ({TEXT_ONLY_LINHA})")
    write_fixture(here / ENCRYPTED_FIXTURE, ENCRYPTED_PAYLOAD, ENCRYPTED_PASSWORD)
    print(f"wrote {ENCRYPTED_FIXTURE}  ({ENCRYPTED_PAYLOAD}, password {ENCRYPTED_PASSWORD!r})")
    return 0


if __name__ == '__main__':
    sys.exit(main())
