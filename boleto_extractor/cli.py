#!/usr/bin/env python3
"""
Command Line Interface for Brazilian Boleto Number Extractor

This module provides the command-line interface for the boleto extractor.
"""

import sys
import argparse
import getpass
from pathlib import Path
import logging

# Try to import pyperclip for clipboard functionality
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

from .barcode import format_brl
from .extractor import BoletoExtractor
from .pdf import PasswordRequired, PdfError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def describe(boleto):
    """One line of payment details for --details."""
    parts = [boleto.kind_label]
    if boleto.segment:
        parts.append(boleto.segment)
    parts.append(format_brl(boleto.amount) if boleto.amount is not None else 'amount not specified')
    if boleto.due_date:
        parts.append(f"due {boleto.due_date.strftime('%d/%m/%Y')}")
    return ', '.join(parts)


def extract_with_prompt(extractor, pdf_path, password):
    """
    Extract, asking for the password on the terminal if the PDF needs one and
    none was given. A prompted password stays out of shell history and `ps`.
    """
    try:
        return extractor.extract(pdf_path, password)
    except PasswordRequired:
        if password or not sys.stdin.isatty():
            raise
        return extractor.extract(pdf_path, getpass.getpass('PDF password: '))


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
  boleto-extractor boleto.pdf --details
  boleto-extractor boleto.pdf --clipboard
  boleto-extractor encrypted.pdf                       (prompts for the password)
  boleto-extractor encrypted.pdf --password mypassword --verbose --format --clipboard
        """
    )

    parser.add_argument(
        'pdf_file',
        help='Path to the PDF file containing the boleto'
    )

    parser.add_argument(
        '--password', '-p',
        type=str,
        help='Password for encrypted PDF files. If omitted, you are prompted when one is needed'
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

    parser.add_argument(
        '--details', '-d',
        action='store_true',
        help='Also print the type, amount and due date of each boleto'
    )

    parser.add_argument(
        '--clipboard', '-c',
        action='store_true',
        help='Copy the first boleto number to clipboard'
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
        boletos = extract_with_prompt(extractor, str(pdf_path), args.password)
    except PdfError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        sys.exit(1)

    if not boletos:
        print("No boleto numbers found.")
        return

    print(f"Found {len(boletos)} boleto number(s):")
    print("-" * 50)

    for boleto in boletos:
        print(boleto.formatted if args.format else boleto.linha)
        if args.details:
            print(f"  {describe(boleto)}")

    print("-" * 50)

    # Copy to clipboard if requested
    if args.clipboard:
        if not CLIPBOARD_AVAILABLE:
            logger.warning("pyperclip not installed. Install with: pip install pyperclip")
        else:
            try:
                # Copy the first boleto number to clipboard
                first = boletos[0]
                clipboard_text = first.formatted if args.format else first.linha
                pyperclip.copy(clipboard_text)
                print(f"✓ Copied to clipboard: {clipboard_text}")
            except Exception as e:
                logger.error(f"Failed to copy to clipboard: {e}")


if __name__ == "__main__":
    main()
