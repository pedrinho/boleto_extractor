#!/usr/bin/env python3
"""
Example usage of the Brazilian Boleto Number Extractor

This script demonstrates how to use the BoletoExtractor class
programmatically in your own Python applications.
"""

from boleto_extractor import BoletoExtractor
import sys

def example_usage():
    """Demonstrate programmatic usage of the BoletoExtractor."""
    
    # Create an instance of the extractor
    extractor = BoletoExtractor()
    
    print("Brazilian Boleto Number Extractor - Example Usage")
    print("=" * 55)
    
    # Example 1: Extract from text
    print("\n1. Extracting boleto numbers from text:")
    sample_text = """
    Boleto Bancário
    Código: 00193373700000001000500940144816060680935031
    Valor: R$ 150,00
    Vencimento: 20/12/2024
    """
    
    numbers = extractor.find_boleto_numbers_in_text(sample_text)
    print(f"Text: {sample_text.strip()}")
    print(f"Found {len(numbers)} boleto number(s):")
    for i, number in enumerate(numbers, 1):
        formatted = extractor.format_boleto_number(number)
        print(f"  {i}. {formatted}")
    
    # Example 2: Validate boleto numbers
    print("\n2. Validating boleto numbers:")
    test_numbers = [
        "00193373700000001000500940144816060680935031",
        "23793381286000042335909000463305975620000335000",
        "123456789",  # Invalid
        "abcdefghijklmnopqrstuvwxyz"  # Invalid
    ]
    
    for number in test_numbers:
        is_valid = extractor.is_valid_boleto_number(number)
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"  {status}: {number}")
    
    # Example 3: Extract from PDF file (if provided as argument)
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"\n3. Extracting from PDF file: {pdf_path}")
        
        try:
            numbers = extractor.extract_boleto_numbers(pdf_path)
            
            if numbers:
                print(f"Found {len(numbers)} boleto number(s):")
                for i, number in enumerate(numbers, 1):
                    formatted = extractor.format_boleto_number(number)
                    print(f"  {i}. {formatted}")
            else:
                print("No boleto numbers found in the PDF")
                
        except Exception as e:
            print(f"Error processing PDF: {e}")
    else:
        print("\n3. To extract from a PDF file, run:")
        print("   python example_usage.py path/to/boleto.pdf")

def batch_processing_example():
    """Example of processing multiple PDF files."""
    
    print("\n" + "=" * 55)
    print("Batch Processing Example")
    print("=" * 55)
    
    # This is a conceptual example - you would replace this with actual file paths
    pdf_files = [
        # "boleto1.pdf",
        # "boleto2.pdf", 
        # "boleto3.pdf"
    ]
    
    extractor = BoletoExtractor()
    results = {}
    
    for pdf_file in pdf_files:
        try:
            print(f"\nProcessing: {pdf_file}")
            numbers = extractor.extract_boleto_numbers(pdf_file)
            results[pdf_file] = numbers
            
            if numbers:
                print(f"  Found {len(numbers)} boleto number(s)")
                for i, number in enumerate(numbers, 1):
                    print(f"    {i}. {number}")
            else:
                print("  No boleto numbers found")
                
        except Exception as e:
            print(f"  Error: {e}")
            results[pdf_file] = []
    
    # Summary
    print(f"\nSummary:")
    total_files = len(results)
    total_numbers = sum(len(numbers) for numbers in results.values())
    print(f"  Files processed: {total_files}")
    print(f"  Total boleto numbers found: {total_numbers}")

if __name__ == "__main__":
    example_usage()
    batch_processing_example() 