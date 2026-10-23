"""
Brazilian Boleto Number Extractor

A Python library to extract boleto numbers from Brazilian boleto PDF files.
"""

from .barcode import BoletoInfo
from .extractor import BoletoExtractor
from .pdf import InvalidPdf, PasswordRequired, PdfError, WrongPassword

__version__ = "2.0.0"
__author__ = "Pedro"
__email__ = ""

__all__ = [
    "BoletoExtractor",
    "BoletoInfo",
    "PdfError",
    "InvalidPdf",
    "PasswordRequired",
    "WrongPassword",
    "extract_boleto_numbers",
    "find_boleto_numbers_in_text",
    "is_valid_boleto_number",
]

# Convenience function for quick extraction
def extract_boleto_numbers(pdf_path, password=None):
    """
    Convenience function to extract boleto numbers from a PDF file.

    Args:
        pdf_path (str): Path to the PDF file
        password (str, optional): Password for encrypted PDF files

    Returns:
        list: List of extracted boleto numbers (linha digitável)
    """
    return BoletoExtractor().extract_boleto_numbers(pdf_path, password)

def find_boleto_numbers_in_text(text):
    """
    Convenience function to find boleto numbers in text.

    Args:
        text (str): Text to search for a printed linha digitável

    Returns:
        list: The 44-digit barcodes of the boletos found
    """
    return BoletoExtractor().find_boleto_numbers_in_text(text)

def is_valid_boleto_number(number):
    """
    Convenience function to validate a boleto barcode.

    Args:
        number (str): 44-digit barcode to validate

    Returns:
        bool: True if valid, False otherwise
    """
    return BoletoExtractor().is_valid_boleto_number(number)
