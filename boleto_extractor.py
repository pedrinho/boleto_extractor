#!/usr/bin/env python3
"""
Brazilian Boleto Number Extractor - Legacy Script

This script provides backward compatibility for the old command-line interface.
For new projects, it's recommended to use the package directly:

    from boleto_extractor import BoletoExtractor
    # or
    from boleto_extractor import extract_boleto_numbers
"""

import sys
import os

# Add the current directory to Python path to import the package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from boleto_extractor.cli import main
except ImportError:
    print("Error: Could not import boleto_extractor package.")
    print("Please ensure the package is properly installed or the files are in the correct location.")
    sys.exit(1)

if __name__ == "__main__":
    main() 