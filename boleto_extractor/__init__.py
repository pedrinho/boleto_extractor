"""
Brazilian Boleto Number Extractor

A Python library to extract boleto numbers from Brazilian boleto PDF files.
"""

from .extractor import BoletoExtractor

__version__ = "1.0.0"
__author__ = "Pedro"
__email__ = ""

# Main class to import
__all__ = ["BoletoExtractor"]

# Convenience function for quick extraction
def extract_boleto_numbers(pdf_path, verbose=False, format_output=False):
    """
    Convenience function to extract boleto numbers from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        verbose (bool): Enable verbose logging
        format_output (bool): Format the output with spaces
        
    Returns:
        list: List of extracted boleto numbers
    """
    extractor = BoletoExtractor()
    return extractor.extract_boleto_numbers(pdf_path)

def find_boleto_numbers_in_text(text):
    """
    Convenience function to find boleto numbers in text.
    
    Args:
        text (str): Text to search for boleto numbers
        
    Returns:
        list: List of found boleto numbers
    """
    extractor = BoletoExtractor()
    return extractor.find_boleto_numbers_in_text(text)

def is_valid_boleto_number(number):
    """
    Convenience function to validate a boleto number.
    
    Args:
        number (str): Boleto number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    extractor = BoletoExtractor()
    return extractor.is_valid_boleto_number(number) 