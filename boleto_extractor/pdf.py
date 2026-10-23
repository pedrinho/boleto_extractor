"""
PDF access for the extractor, on PyMuPDF alone.

An uploaded PDF is attacker-controlled input and rendering it is the one expensive
thing this package does, so the limits that keep a hostile file from exhausting
memory live here: a cap on pages and a cap on pixels per rendered page.
"""

import math
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Union

import numpy as np
import pymupdf

# Boletos are one or two pages; carnês (payment booklets) run to about a dozen.
MAX_PAGES = 20

# Pixels rendered for one page, at most. A small file can declare a 200-inch page,
# which at full zoom would need gigabytes. Holds an A4 page at RENDER_ZOOM.
MAX_PIXELS = 12_000_000

# Zoom at which the narrow bars of an Interleaved 2 of 5 barcode decode reliably.
RENDER_ZOOM = 3.0

# The PDF header may sit anywhere in the first 1024 bytes.
_HEADER_WINDOW = 1024


class PdfError(Exception):
    """A PDF that cannot be processed. Messages are written for end users."""


class InvalidPdf(PdfError):
    def __init__(self):
        super().__init__("This file could not be read as a PDF.")


class PasswordRequired(PdfError):
    def __init__(self):
        super().__init__("This PDF is password protected. Enter its password and try again.")


class WrongPassword(PdfError):
    def __init__(self):
        super().__init__("The password is incorrect for this PDF.")


@contextmanager
def open_pdf(source: Union[str, Path, bytes], password: Optional[str] = None) -> Iterator[pymupdf.Document]:
    """
    Open a PDF from a path or from bytes, unlocking it with `password` if needed.

    Raises InvalidPdf, PasswordRequired or WrongPassword; a missing path raises
    FileNotFoundError. Uploads are opened from memory and never touch disk.
    """
    if isinstance(source, (bytes, bytearray)):
        data = bytes(source)
    else:
        data = Path(source).read_bytes()
    if b'%PDF-' not in data[:_HEADER_WINDOW]:
        raise InvalidPdf()

    try:
        doc = pymupdf.open(stream=data, filetype='pdf')
    except RuntimeError as e:  # MuPDF's errors, FileDataError included
        raise InvalidPdf() from e

    try:
        if doc.needs_pass:
            if not password:
                raise PasswordRequired()
            if not doc.authenticate(password):
                raise WrongPassword()
        yield doc
    finally:
        doc.close()


def _pages(doc: pymupdf.Document) -> Iterator[pymupdf.Page]:
    for number in range(min(doc.page_count, MAX_PAGES)):
        yield doc.load_page(number)


def iter_page_text(doc: pymupdf.Document) -> Iterator[str]:
    """Yield the text of each page, up to MAX_PAGES."""
    for page in _pages(doc):
        yield page.get_text()


def iter_page_images(doc: pymupdf.Document) -> Iterator[np.ndarray]:
    """
    Yield each page, up to MAX_PAGES, rendered as a grayscale array. One page is
    held at a time, and each is scaled down as needed to stay within MAX_PIXELS.
    """
    for page in _pages(doc):
        area = page.rect.width * page.rect.height
        if area <= 0:
            continue
        zoom = min(RENDER_ZOOM, math.sqrt(MAX_PIXELS / area))
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), colorspace=pymupdf.csGRAY, alpha=False)
        # Rows may be padded beyond the image width; drop the padding.
        rows = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.stride)
        yield rows[:, :pix.width]
