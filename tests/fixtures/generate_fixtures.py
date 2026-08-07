#!/usr/bin/env python3
"""
Regenerate the boleto PDF fixtures used by tests/test_integration.py.

Real boletos carry payment data, so the fixtures are synthetic: each one renders a
known 44-digit payload as a genuine Interleaved 2 of 5 barcode (the symbology
Brazilian boletos use) into a PDF. Because the payload is known up front, the tests
can assert an exact expected result rather than whatever the decoder happens to say.

Usage:
    venv/bin/python tests/fixtures/generate_fixtures.py
"""

import sys
from pathlib import Path

import fitz  # PyMuPDF

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

# The payloads under test. Each is a 44-digit barcode; the first is the one the
# existing unit tests already use, so its expected output is independently known.
FIXTURES = {
    'boleto_bradesco.pdf': '19797116900000386000000004572849356277103564',
    'boleto_bb.pdf':       '00191234500000150000000123456789012345678901',
    'boleto_itau.pdf':     '34191098700002500001234567890123456789012345',
}


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


def write_fixture(path: Path, payload: str) -> None:
    elements = list(_elements(payload))
    symbol_width = sum(width for width, _ in elements)

    doc = fitz.open()
    page = doc.new_page(
        width=symbol_width + 2 * MARGIN,
        height=BAR_HEIGHT + 2 * MARGIN + 40,
    )

    # A little context text, so the fixture also exercises the text-extraction path.
    page.insert_text((MARGIN, MARGIN - 12), "Boleto de teste - fixture sintetica", fontsize=10)

    x = MARGIN
    for width, is_bar in elements:
        if is_bar:
            rect = fitz.Rect(x, MARGIN, x + width, MARGIN + BAR_HEIGHT)
            page.draw_rect(rect, color=None, fill=(0, 0, 0))
        x += width

    doc.save(str(path))
    doc.close()


def main() -> int:
    here = Path(__file__).parent
    for name, payload in FIXTURES.items():
        write_fixture(here / name, payload)
        print(f"wrote {name}  ({payload})")
    return 0


if __name__ == '__main__':
    sys.exit(main())
