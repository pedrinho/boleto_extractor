#!/usr/bin/env python3
"""
Brazilian Boleto Number Extractor

This module contains the main BoletoExtractor class for extracting
boleto numbers from Brazilian boleto PDF files.
"""

import re
import logging
from typing import List, Optional, Tuple
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

# Configure logging
logger = logging.getLogger(__name__)

class BoletoExtractor:
    """Extract boleto numbers from Brazilian boleto PDF files."""
    
    def __init__(self):
        # Common patterns for Brazilian boleto barcodes (44 digits)
        self.boleto_patterns = [
            # Standard 44-digit barcode
            r'\b\d{44}\b',
            # Barcode format: starts with specific bank codes
            r'\b(001|033|104|237|341|356|389|422|633|745|756|000|004|021|025|077|085|097|212|318|197)\d{43}\b',
        ]
        
        # Common boleto keywords to help identify relevant text
        self.boleto_keywords = [
            'boleto', 'código', 'bancário', 'pagamento',
            'valor', 'vencimento', 'beneficiário', 'cedente', 'sacado'
        ]

    def extract_text_from_pdf(self, pdf_path: str, password: str = None) -> str:
        """
        Extract text from PDF using multiple methods for better accuracy.
        
        Args:
            pdf_path (str): Path to the PDF file
            password (str, optional): Password for encrypted PDF files
            
        Returns:
            str: Extracted text content
        """
        text_content = []
        
        # Method 1: Try pdfplumber first
        try:
            with pdfplumber.open(pdf_path, password=password) as pdf:
                for i, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                    except Exception:
                        continue
        except Exception:
            pass
        
        # Method 2: Try PyPDF2 as backup
        if not text_content:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    if pdf_reader.is_encrypted:
                        if password:
                            try:
                                pdf_reader.decrypt(password)
                            except Exception as e:
                                logger.error(f"Failed to decrypt PDF with provided password: {e}")
                                return ""
                        else:
                            try:
                                pdf_reader.decrypt('')
                            except Exception:
                                return ""
                    
                    # Extract text from all pages
                    for i, page in enumerate(pdf_reader.pages):
                        try:
                            text = page.extract_text()
                            if text:
                                text_content.append(text)
                        except Exception:
                            continue
            except Exception:
                pass
        
        return '\n'.join(text_content)

    def convert_pdf_to_images(self, pdf_path: str, password: str = None) -> List[np.ndarray]:
        """
        Convert PDF pages to images for barcode scanning.
        
        Args:
            pdf_path (str): Path to the PDF file
            password (str, optional): Password for encrypted PDF files
            
        Returns:
            List[np.ndarray]: List of images as numpy arrays
        """
        images = []
        
        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(pdf_path)
                
                if doc.needs_pass:
                    if password:
                        try:
                            doc.authenticate(password)
                        except Exception as e:
                            logger.error(f"Failed to decrypt PDF with provided password: {e}")
                            doc.close()
                            return images
                    else:
                        doc.close()
                        return images
                
                for page_num in range(len(doc)):
                    try:
                        page = doc.load_page(page_num)
                        # Higher resolution for better barcode detection
                        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
                        img_data = pix.tobytes("png")
                        
                        # Convert to numpy array
                        img = Image.open(io.BytesIO(img_data))
                        img_array = np.array(img)
                        
                        # Convert to grayscale if it's RGB
                        if len(img_array.shape) == 3:
                            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                        
                        images.append(img_array)
                        
                    except Exception:
                        continue
                
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
        """
        Find 44-digit boleto barcodes in text using regex patterns.
        
        Args:
            text (str): Text to search for boleto barcodes
            
        Returns:
            List[str]: List of found 44-digit boleto barcodes
        """
        if not text:
            return []
        
        # Patterns for 44-digit boleto barcodes only
        patterns = [
            # Standard 44-digit barcode
            r'\b\d{44}\b',
            # Barcode format: starts with specific bank codes
            r'\b(001|033|104|237|341|356|389|422|633|745|756|000|004|021|025|077|085|097|212|318|197)\d{43}\b',
        ]
        
        found_numbers = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean the match (remove spaces, dashes, dots)
                clean_match = re.sub(r'[\s\-\.]', '', match)
                
                # Only accept 44-digit numbers that start with valid bank codes
                if len(clean_match) == 44 and self.is_valid_boleto_number(clean_match):
                    found_numbers.append(clean_match)
        
        # Remove duplicates while preserving order
        unique_numbers = []
        for num in found_numbers:
            if num not in unique_numbers:
                unique_numbers.append(num)
        
        return unique_numbers
    
    def extract_from_raw_pdf_content(self, pdf_path: str, password: str = None) -> List[str]:
        """Extract 44-digit boleto barcodes from raw PDF content, useful for encrypted PDFs."""
        found_numbers = []
        try:
            with open(pdf_path, 'rb') as file:
                content = file.read()
            content_str = content.decode('latin-1', errors='ignore')
            
            # Only look for 44-digit barcodes
            pattern = r'\b\d{44}\b'
            matches = re.findall(pattern, content_str)
            
            for match in matches:
                if self.is_valid_boleto_number(match):
                    found_numbers.append(match)
                
        except Exception as e:
            logger.error(f"Error extracting from raw PDF content: {e}")
        
        return found_numbers

    def is_valid_boleto_number(self, number: str) -> bool:
        """
        Validate if a number is a valid Brazilian boleto barcode (44 digits).
        Returns True for any 44-digit number, with warnings for unknown bank codes.
        
        Args:
            number (str): Number to validate
            
        Returns:
            bool: True if valid 44-digit number, False otherwise
        """
        if not number or not number.isdigit():
            return False
        
        # Only accept 44-digit barcodes
        if len(number) != 44:
            return False
        
        # Check if it starts with a known Brazilian bank code
        known_bank_codes = [
            '001', '033', '104', '237', '341', '356', '389', '422', 
            '633', '745', '756', '000', '004', '021', '025', '077', 
            '085', '097', '212', '318', '197'
        ]
        
        if len(number) >= 3 and number[:3] in known_bank_codes:
            return True
        else:
            # Unknown bank code, but still return True with a warning
            logger.warning(f"Unknown bank code '{number[:3]}' in boleto number: {number}")
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

    def scan_barcodes_in_pdf(self, pdf_path: str, password: str = None) -> List[str]:
        """
        Scan for barcodes in PDF pages.
        
        Args:
            pdf_path (str): Path to the PDF file
            password (str, optional): Password for encrypted PDF files
            
        Returns:
            List[str]: List of found barcode numbers
        """
        barcode_numbers = []
        
        if PYMUPDF_AVAILABLE:
            page_images = self.convert_pdf_to_images(pdf_path, password)
            
            for i, img in enumerate(page_images):
                try:
                    # Find barcodes in the image
                    barcodes = pyzbar.decode(img)
                    
                    for barcode in barcodes:
                        barcode_data = barcode.data.decode('utf-8')
                        
                        # Check if it looks like a boleto number
                        if self.is_valid_boleto_number(barcode_data):
                            barcode_numbers.append(barcode_data)
                    
                except Exception:
                    continue
        
        return barcode_numbers

    def barcode_to_linha_digitavel(self, barcode: str) -> Optional[str]:
        """
        Convert a 44-digit boleto barcode to the 47-digit linha digitável.
        Returns None if the input is not 44 digits.
        """
        if not barcode or len(barcode) != 44 or not barcode.isdigit():
            return None
        # Bank boletos (first digit != 8)
        if barcode[0] != '8':
            # Fields:
            # 1: 1-4 (bank+currency) + 20-24 (5 digits)
            # 2: 25-34 (10 digits)
            # 3: 35-44 (10 digits)
            # General structure: AAAAA BBBBB CCCCCCCCCC DDDDDDDDDD EEEEEEEEEE F
            # Where F is the general check digit (barcode[4])
            # Linha digitável: 5 10 10 1 15 = 47
            def calc_mod10(block):
                s = 0
                mult = 2
                for d in reversed(block):
                    add = int(d) * mult
                    if add > 9:
                        add = (add // 10) + (add % 10)
                    s += add
                    mult = 1 if mult == 2 else 2
                dv = (10 - (s % 10)) % 10
                return str(dv)
            # Field 1
            f1 = barcode[0:4] + barcode[19:24]
            f1_dv = calc_mod10(f1)
            # Field 2
            f2 = barcode[24:34]
            f2_dv = calc_mod10(f2)
            # Field 3
            f3 = barcode[34:44]
            f3_dv = calc_mod10(f3)
            # Field 4: general check digit
            f4 = barcode[4]
            # Field 5: due date factor + value
            f5 = barcode[5:19]
            return f"{f1}{f1_dv}{f2}{f2_dv}{f3}{f3_dv}{f4}{f5}"
        # For convenience, return None for non-bank boletos (convenio/arrecadacao)
        return None

    def extract_boleto_numbers(self, pdf_path: str, password: str = None) -> List[str]:
        """
        Extract boleto numbers from a PDF file by reading barcodes and converting to linha digitável.
        
        Args:
            pdf_path (str): Path to the PDF file
            password (str, optional): Password for encrypted PDF files
            
        Returns:
            List[str]: List of extracted 47-digit boleto numbers (linha digitável)
        """
        all_numbers = []
        
        # Method 1: Scan barcodes (primary method)
        barcode_numbers = self.scan_barcodes_in_pdf(pdf_path, password)
        all_numbers.extend(barcode_numbers)
        
        # Method 2: Extract text and look for 44-digit barcodes (backup)
        if not all_numbers:
            text = self.extract_text_from_pdf(pdf_path, password)
            if text:
                text_numbers = self.find_boleto_numbers_in_text(text)
                all_numbers.extend(text_numbers)
        
        # Method 3: Try to extract from raw PDF content (for encrypted PDFs)
        if not all_numbers:
            raw_numbers = self.extract_from_raw_pdf_content(pdf_path, password)
            all_numbers.extend(raw_numbers)
        
        # Remove duplicates while preserving order
        unique_numbers = []
        for num in all_numbers:
            if num not in unique_numbers:
                unique_numbers.append(num)
        
        # Convert all 44-digit barcodes to 47-digit linha digitável
        result = []
        for num in unique_numbers:
            if len(num) == 44:
                # Convert 44-digit barcode to 47-digit linha digitável
                linha = self.barcode_to_linha_digitavel(num)
                if linha:
                    result.append(linha)
            elif len(num) == 47:
                # Already a 47-digit number, keep as is
                result.append(num)
        
        return result

    def format_boleto_number(self, number: str) -> str:
        """
        Format a 47-digit boleto number in Brazilian "linha digitável" format.
        
        Args:
            number (str): 47-digit boleto number to format
            
        Returns:
            str: Formatted boleto number in Brazilian standard format
        """
        if not number or len(number) != 47:
            return number
        
        # Brazilian "linha digitável" format: XXXXX.XXXXX XXXXX.XXXXXX XXXXX.XXXXXX X XXXXXXXXXXXXXX
        # Field 1: positions 1-5 (5 digits) + positions 6-10 (5 digits) = XXXXX.XXXXX
        # Field 2: positions 11-15 (5 digits) + positions 16-20 (5 digits) = XXXXX.XXXXX  
        # Field 3: positions 21-25 (5 digits) + positions 26-30 (5 digits) = XXXXX.XXXXX
        # Field 4: position 31 (1 digit) = X
        # Field 5: positions 32-47 (16 digits) = XXXXXXXXXXXXXXXX
        
        field1 = number[0:5] + "." + number[5:10]      # XXXXX.XXXXX
        field2 = number[10:15] + "." + number[15:20]   # XXXXX.XXXXX
        field3 = number[20:25] + "." + number[25:30]   # XXXXX.XXXXX
        field4 = number[30]                             # X
        field5 = number[31:47]                          # XXXXXXXXXXXXXXXX
        
        return f"{field1} {field2} {field3} {field4} {field5}" 