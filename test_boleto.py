#!/usr/bin/env python3
"""
Test script for the Brazilian Boleto Number Extractor

This script demonstrates how the boleto extractor works with sample data.
"""

from boleto_extractor import BoletoExtractor

def test_boleto_extractor():
    """Test the boleto extractor with sample data."""
    
    # Create extractor instance
    extractor = BoletoExtractor()
    
    # Sample boleto numbers (these are examples, not real boleto numbers)
    sample_texts = [
        # Sample 1: 47-digit boleto
        "Boleto Bancário - Código: 00193373700000001000500940144816060680935031",
        
        # Sample 2: 44-digit boleto
        "Linha digitável: 23793381286000042335909000463305975620000335000",
        
        # Sample 3: Formatted boleto
        "Código de barras: 00190 00090 30144816 06068 09350 31",
        
        # Sample 4: Mixed text with multiple boleto numbers
        """
        Boleto 1: 00193373700000001000500940144816060680935031
        Boleto 2: 23793381286000042335909000463305975620000335000
        Valor: R$ 100,00
        Vencimento: 15/12/2024
        """
    ]
    
    print("Testing Brazilian Boleto Number Extractor")
    print("=" * 50)
    
    for i, text in enumerate(sample_texts, 1):
        print(f"\nTest {i}:")
        print(f"Input text: {text.strip()}")
        
        # Find boleto numbers in the text
        numbers = extractor.find_boleto_numbers_in_text(text)
        
        if numbers:
            print(f"Found {len(numbers)} boleto number(s):")
            for j, number in enumerate(numbers, 1):
                formatted = extractor.format_boleto_number(number)
                print(f"  {j}. {formatted}")
        else:
            print("No boleto numbers found")
        
        print("-" * 30)
    
    # Test validation function
    print("\nTesting boleto number validation:")
    test_numbers = [
        "00193373700000001000500940144816060680935031",  # Valid 47-digit
        "23793381286000042335909000463305975620000335000",  # Valid 44-digit
        "12345678901234567890123456789012345678901234567",  # Valid 47-digit (unknown bank)
        "123456789",  # Invalid (too short)
        "abcdefghijklmnopqrstuvwxyz",  # Invalid (not digits)
        "0019337370000000100050094014481606068093503",  # Invalid (46 digits)
    ]
    
    for number in test_numbers:
        is_valid = extractor.is_valid_boleto_number(number)
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"{status}: {number}")

if __name__ == "__main__":
    test_boleto_extractor() 