#!/usr/bin/env python3
"""
Brazilian Boleto Number Extractor

This module contains the BoletoExtractor class, which finds the boletos in a PDF.
The rules for barcodes and linhas digitáveis live in barcode.py and the PDF
handling in pdf.py; this class ties the two together.
"""

from datetime import date
from pathlib import Path
from typing import List, Optional, Union

import zxingcpp

from .barcode import (
    BoletoInfo,
    barcode_to_linha,
    decode,
    find_barcodes_in_text,
    format_linha,
    is_valid_barcode,
)
from .pdf import iter_page_images, iter_page_text, open_pdf


class BoletoExtractor:
    """Extract boleto numbers from Brazilian boleto PDF files."""

    def extract(
        self,
        source: Union[str, Path, bytes],
        password: Optional[str] = None,
        today: Optional[date] = None,
    ) -> List[BoletoInfo]:
        """
        Find the boletos in a PDF, given as a path or as bytes.

        The printed linha digitável is read from the text first: it is cheap and
        its check digits make it trustworthy. Only if no page has one are the pages
        rendered and scanned for barcodes.

        Raises pdf.PdfError subclasses for unreadable or locked PDFs, and
        FileNotFoundError for a missing path. `today` is passed to barcode.decode.
        """
        with open_pdf(source, password) as doc:
            barcodes = []
            for text in iter_page_text(doc):
                barcodes.extend(find_barcodes_in_text(text))
            if not barcodes:
                for image in iter_page_images(doc):
                    barcodes.extend(self._scan_barcodes(image))

        unique = list(dict.fromkeys(barcodes))
        return [decode(b, today) for b in unique]

    @staticmethod
    def _scan_barcodes(image) -> List[str]:
        # Boleto barcodes are always Interleaved 2 of 5; restricting the format
        # avoids false positives from other symbologies.
        results = zxingcpp.read_barcodes(image, formats=zxingcpp.BarcodeFormat.ITF)
        return [r.text for r in results if is_valid_barcode(r.text)]

    def extract_boleto_numbers(self, pdf_path: Union[str, Path, bytes], password: Optional[str] = None) -> List[str]:
        """
        Extract boleto numbers (linha digitável) from a PDF: 47 digits for bank
        boletos, 48 digits for arrecadação boletos. Raises like extract().
        """
        return [boleto.linha for boleto in self.extract(pdf_path, password)]

    def find_boleto_numbers_in_text(self, text: str) -> List[str]:
        """Return the 44-digit barcodes of the boletos whose linha digitável appears in `text`."""
        return find_barcodes_in_text(text)

    def is_valid_boleto_number(self, number: str) -> bool:
        """True if `number` is a 44-digit boleto barcode with a correct check digit."""
        return is_valid_barcode(number)

    def barcode_to_linha_digitavel(self, barcode: str) -> Optional[str]:
        """Convert a 44-digit barcode to its 47-digit (bank) or 48-digit (arrecadação) linha digitável."""
        return barcode_to_linha(barcode)

    def format_boleto_number(self, number: str) -> str:
        """Group a 47- or 48-digit linha digitável as printed on the boleto."""
        return format_linha(number)
