#!/usr/bin/env python3
"""
Tests for boleto_extractor.pdf: opening, passwords, and the resource limits that
protect the server from hostile uploads. PDFs are built in memory with PyMuPDF.
"""

import unittest
from pathlib import Path

import pymupdf

from boleto_extractor.pdf import (
    MAX_PAGES,
    MAX_PIXELS,
    InvalidPdf,
    PasswordRequired,
    WrongPassword,
    iter_page_images,
    iter_page_text,
    open_pdf,
)

FIXTURES = Path(__file__).parent / 'fixtures'
ENCRYPTED = FIXTURES / 'boleto_encrypted.pdf'


def make_pdf(pages=1, width=595, height=842, text=None):
    doc = pymupdf.open()
    for _ in range(pages):
        page = doc.new_page(width=width, height=height)
        if text:
            page.insert_text((50, 50), text)
    data = doc.tobytes()
    doc.close()
    return data


class TestOpen(unittest.TestCase):

    def test_opens_bytes_and_paths(self):
        with open_pdf(make_pdf(text='hello')) as doc:
            self.assertIn('hello', next(iter_page_text(doc)))
        with open_pdf(FIXTURES / 'boleto_bradesco.pdf') as doc:
            self.assertEqual(doc.page_count, 1)
        with open_pdf(str(FIXTURES / 'boleto_bradesco.pdf')) as doc:
            self.assertEqual(doc.page_count, 1)

    def test_not_a_pdf(self):
        for data in (b'', b'not a pdf', b'GIF89a' + b'\0' * 100, b'%PDF-1.7 truncated'):
            with self.subTest(data=data[:20]):
                with self.assertRaises(InvalidPdf):
                    with open_pdf(data):
                        pass

    def test_missing_path(self):
        with self.assertRaises(FileNotFoundError):
            with open_pdf(FIXTURES / 'does_not_exist.pdf'):
                pass

    def test_password_required(self):
        with self.assertRaises(PasswordRequired):
            with open_pdf(ENCRYPTED):
                pass

    def test_wrong_password(self):
        with self.assertRaises(WrongPassword):
            with open_pdf(ENCRYPTED, 'wrong'):
                pass

    def test_right_password(self):
        with open_pdf(ENCRYPTED, 'secret') as doc:
            self.assertEqual(len(list(iter_page_images(doc))), 1)

    def test_messages_are_fit_for_users(self):
        self.assertIn('password', str(PasswordRequired()).lower())
        self.assertIn('incorrect', str(WrongPassword()))
        self.assertIn('PDF', str(InvalidPdf()))


class TestLimits(unittest.TestCase):

    def test_page_cap(self):
        with open_pdf(make_pdf(pages=MAX_PAGES + 30)) as doc:
            self.assertEqual(len(list(iter_page_text(doc))), MAX_PAGES)
            self.assertEqual(sum(1 for _ in iter_page_images(doc)), MAX_PAGES)

    def test_huge_page_is_scaled_down(self):
        # The largest page the PDF spec allows: 200 x 200 inches. At full zoom
        # this would be 43200 x 43200 pixels, almost 2GB.
        with open_pdf(make_pdf(width=14400, height=14400)) as doc:
            image = next(iter_page_images(doc))
        self.assertLessEqual(image.size, MAX_PIXELS * 1.01)

    def test_a4_page_renders_at_full_zoom(self):
        with open_pdf(make_pdf()) as doc:
            image = next(iter_page_images(doc))
        self.assertEqual(image.shape, (2526, 1785))  # 842 x 595 points at 3x
        self.assertEqual(image.ndim, 2)  # grayscale


if __name__ == '__main__':
    unittest.main()
