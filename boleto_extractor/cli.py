#!/usr/bin/env python3
"""
Command Line Interface for Brazilian Boleto Number Extractor

This module provides the command-line interface for the boleto extractor.
"""

import sys
import argparse
from pathlib import Path
import logging

from .extractor import BoletoExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main function to handle command line arguments and run the extractor."""
    parser = argparse.ArgumentParser(
        description="Extract boleto numbers from Brazilian boleto PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  boleto-extractor boleto.pdf
  boleto-extractor /path/to/boleto.pdf --verbose
  boleto-extractor boleto.pdf --format
  boleto-extractor encrypted.pdf --password mypassword
  boleto-extractor encrypted.pdf --password mypassword --verbose --format
        """
    )
    
    parser.add_argument(
        'pdf_file',
        help='Path to the PDF file containing the boleto'
    )
    
    parser.add_argument(
        '--password', '-p',
        type=str,
        help='Password for encrypted PDF files'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--format', '-f',
        action='store_true',
        help='Format the output with spaces for readability'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if file exists
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        logger.error(f"File not found: {pdf_path}")
        sys.exit(1)
    
    if not pdf_path.suffix.lower() == '.pdf':
        logger.error(f"File is not a PDF: {pdf_path}")
        sys.exit(1)
    
    # Create extractor and process file
    extractor = BoletoExtractor()
    
    try:
        boleto_numbers = extractor.extract_boleto_numbers(str(pdf_path), args.password)
        
        if not boleto_numbers:
            print("No boleto numbers found.")
        else:
            print(f"Found {len(boleto_numbers)} boleto number(s):")
            print("-" * 50)
            
            for number in boleto_numbers:
                if args.format:
                    formatted_number = extractor.format_boleto_number(number)
                    print(formatted_number)
                else:
                    print(number)
            
            print("-" * 50)
            
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 