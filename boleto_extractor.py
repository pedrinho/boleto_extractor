#!/usr/bin/env python3
"""
Brazilian Boleto Number Extractor

This script extracts boleto numbers from Brazilian boleto PDF files.
It uses multiple methods to ensure maximum accuracy:
1. Text extraction from PDF
2. Barcode reading (Code 128, Code 39, etc.)
3. Pattern matching for common boleto formats
4. PDF to image conversion for better barcode detection

Usage:
    python boleto_extractor.py <pdf_file_path>
"""

import sys
import re
import argparse
from pathlib import Path
from typing import List, Optional, Tuple
import logging
import tempfile
import os
import io

# PDF processing
import pdfplumber
import PyPDF2

# Image processing and barcode reading
import cv2
import numpy as np
from PIL import Image
from pyzbar import pyzbar

# PDF to image conversion
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warning: PyMuPDF not available. Install with: pip install PyMuPDF")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BoletoExtractor:
    """Extract boleto numbers from Brazilian boleto PDF files."""
    
    def __init__(self):
        # Common patterns for Brazilian boleto numbers
        self.boleto_patterns = [
            # Standard boleto format: 47 digits
            r'\b\d{47}\b',
            # Alternative format: 44 digits
            r'\b\d{44}\b',
            # Line format: 47 digits with spaces
            r'\b\d{4}\s\d{5}\s\d{10}\s\d{10}\s\d{10}\s\d{2}\s\d{14}\b',
            # Line format: 44 digits with spaces
            r'\b\d{4}\s\d{5}\s\d{10}\s\d{10}\s\d{10}\s\d{5}\b',
            # Barcode format: starts with specific bank codes
            r'\b(001|033|104|237|341|356|389|422|633|745|756|001|033|104|237|341|356|389|422|633|745|756)\d{43}\b',
        ]
        
        # Common boleto keywords to help identify relevant text
        self.boleto_keywords = [
            'boleto', 'código', 'linha', 'digitável', 'bancário', 'pagamento',
            'valor', 'vencimento', 'beneficiário', 'cedente', 'sacado'
        ]

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using multiple methods."""
        text_content = []
        
        try:
            # Method 1: Using pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            
            # Method 2: Using PyPDF2 as backup
            if not text_content:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    # Check if PDF is encrypted
                    if pdf_reader.is_encrypted:
                        logger.warning("PDF is encrypted. Trying to decrypt with empty password...")
                        try:
                            pdf_reader.decrypt('')
                        except:
                            logger.warning("Could not decrypt PDF with empty password")
                            return ""
                    
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
        
        return "\n".join(text_content)

    def convert_pdf_to_images(self, pdf_path: str) -> List[np.ndarray]:
        """Convert PDF pages to images for barcode scanning."""
        images = []
        
        if not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not available. Cannot convert PDF to images.")
            return images
        
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Convert page to image with high resolution
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Convert to numpy array
                img_array = np.array(pil_image)
                images.append(img_array)
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            
        return images

    def extract_images_from_pdf(self, pdf_path: str) -> List[np.ndarray]:
        """Extract images from PDF for barcode scanning."""
        images = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # Extract images from the page
                    page_images = page.images
                    for img in page_images:
                        # Convert to numpy array
                        img_array = np.array(img['stream'])
                        if len(img_array.shape) == 3:
                            images.append(img_array)
                            
        except Exception as e:
            logger.error(f"Error extracting images from PDF: {e}")
            
        return images

    def find_boleto_numbers_in_text(self, text: str) -> List[str]:
        """Find boleto numbers in extracted text using pattern matching."""
        found_numbers = []
        
        # Clean the text
        text = re.sub(r'\s+', ' ', text)
        
        # Try each pattern
        for pattern in self.boleto_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean the match (remove spaces)
                clean_match = re.sub(r'\s', '', match)
                if self.is_valid_boleto_number(clean_match):
                    found_numbers.append(clean_match)
        
        # Remove duplicates while preserving order
        unique_numbers = []
        for num in found_numbers:
            if num not in unique_numbers:
                unique_numbers.append(num)
        
        return unique_numbers

    def is_valid_boleto_number(self, number: str) -> bool:
        """Validate if a number looks like a valid boleto number."""
        if not number or not number.isdigit():
            return False
        
        # Check length (44 or 47 digits)
        if len(number) not in [44, 47]:
            return False
        
        # Check if it starts with a valid bank code (common Brazilian banks)
        valid_bank_codes = [
            '001', '033', '104', '237', '341', '356', '389', '422', '633', '745', '756',
            '000', '004', '021', '025', '077', '085', '097', '212', '318', '341', '356',
            '389', '422', '633', '745', '756', '001', '033', '104', '237', '341', '356',
            '389', '422', '633', '745', '756'
        ]
        
        if len(number) >= 3:
            bank_code = number[:3]
            if bank_code in valid_bank_codes:
                return True
        
        # If it doesn't start with a known bank code, still consider it valid
        # as there might be new banks or different formats
        return True

    def scan_barcodes_in_image(self, image: np.ndarray) -> List[str]:
        """Scan for barcodes in an image."""
        barcode_data = []
        
        try:
            # Convert to PIL Image
            if len(image.shape) == 3:
                pil_image = Image.fromarray(image)
            else:
                pil_image = Image.fromarray(image, mode='L')
            
            # Scan for barcodes
            barcodes = pyzbar.decode(pil_image)
            
            for barcode in barcodes:
                data = barcode.data.decode('utf-8')
                if data and self.is_valid_boleto_number(data):
                    barcode_data.append(data)
                    
        except Exception as e:
            logger.error(f"Error scanning barcodes: {e}")
            
        return barcode_data

    def scan_barcodes_in_pdf(self, pdf_path: str) -> List[str]:
        """Scan for barcodes in all images extracted from PDF."""
        barcode_data = []
        
        try:
            # Method 1: Extract embedded images from PDF
            logger.info("Extracting embedded images from PDF...")
            images = self.extract_images_from_pdf(pdf_path)
            
            # Scan each image for barcodes
            for i, image in enumerate(images):
                barcodes = self.scan_barcodes_in_image(image)
                barcode_data.extend(barcodes)
                if barcodes:
                    logger.info(f"Found {len(barcodes)} barcodes in embedded image {i+1}")
            
            # Method 2: Convert PDF pages to images (if PyMuPDF is available)
            if PYMUPDF_AVAILABLE:
                logger.info("Converting PDF pages to images for barcode scanning...")
                page_images = self.convert_pdf_to_images(pdf_path)
                
                for i, image in enumerate(page_images):
                    barcodes = self.scan_barcodes_in_image(image)
                    barcode_data.extend(barcodes)
                    if barcodes:
                        logger.info(f"Found {len(barcodes)} barcodes in page {i+1}")
                
        except Exception as e:
            logger.error(f"Error scanning barcodes in PDF: {e}")
            
        return barcode_data

    def extract_boleto_numbers(self, pdf_path: str) -> List[str]:
        """Main method to extract boleto numbers from PDF."""
        logger.info(f"Processing PDF: {pdf_path}")
        
        all_numbers = []
        
        # Method 1: Extract from text
        logger.info("Extracting text from PDF...")
        text = self.extract_text_from_pdf(pdf_path)
        if text:
            text_numbers = self.find_boleto_numbers_in_text(text)
            all_numbers.extend(text_numbers)
            logger.info(f"Found {len(text_numbers)} numbers in text")
        else:
            logger.warning("No text could be extracted from PDF")
        
        # Method 2: Scan barcodes
        logger.info("Scanning for barcodes...")
        barcode_numbers = self.scan_barcodes_in_pdf(pdf_path)
        all_numbers.extend(barcode_numbers)
        logger.info(f"Found {len(barcode_numbers)} numbers in barcodes")
        
        # Remove duplicates while preserving order
        unique_numbers = []
        for num in all_numbers:
            if num not in unique_numbers:
                unique_numbers.append(num)
        
        return unique_numbers

    def format_boleto_number(self, number: str) -> str:
        """Format boleto number for display."""
        if len(number) == 47:
            # Format as: XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX X
            return f"{number[:4]} {number[4:8]} {number[8:12]} {number[12:16]} {number[16:20]} {number[20:24]} {number[24:28]} {number[28:32]} {number[32:36]} {number[36:40]} {number[40:44]} {number[44:47]}"
        elif len(number) == 44:
            # Format as: XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX
            return f"{number[:4]} {number[4:8]} {number[8:12]} {number[12:16]} {number[16:20]} {number[20:24]} {number[24:28]} {number[28:32]} {number[32:36]} {number[36:40]} {number[40:44]}"
        else:
            return number


def main():
    """Main function to handle command line arguments and run the extractor."""
    parser = argparse.ArgumentParser(
        description="Extract boleto numbers from Brazilian boleto PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python boleto_extractor.py boleto.pdf
  python boleto_extractor.py /path/to/boleto.pdf --verbose
  python boleto_extractor.py boleto.pdf --format
        """
    )
    
    parser.add_argument(
        'pdf_file',
        help='Path to the PDF file containing the boleto'
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
        boleto_numbers = extractor.extract_boleto_numbers(str(pdf_path))
        
        if not boleto_numbers:
            logger.warning("No boleto numbers found in the PDF")
            print("No boleto numbers found.")
            print("\nPossible reasons:")
            print("- PDF is encrypted/password protected")
            print("- PDF contains only images (no text)")
            print("- Boleto number is not in a recognized format")
            print("- PDF quality is too low for text extraction")
            print("\nTry installing PyMuPDF for better image processing:")
            print("pip install PyMuPDF")
        else:
            logger.info(f"Found {len(boleto_numbers)} boleto number(s)")
            print(f"\nFound {len(boleto_numbers)} boleto number(s):")
            print("-" * 50)
            
            for i, number in enumerate(boleto_numbers, 1):
                if args.format:
                    formatted_number = extractor.format_boleto_number(number)
                    print(f"{i}. {formatted_number}")
                else:
                    print(f"{i}. {number}")
            
            print("-" * 50)
            
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 