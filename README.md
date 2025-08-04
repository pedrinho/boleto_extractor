# Brazilian Boleto Number Extractor

A Python script to extract boleto numbers from Brazilian boleto PDF files. This tool uses multiple methods to ensure maximum accuracy in extracting boleto numbers from various PDF formats.

## Features

- **Multiple Extraction Methods**: Text extraction, barcode scanning, and pattern matching
- **Support for Different Formats**: 44-digit and 47-digit boleto numbers
- **Barcode Detection**: Reads Code 128, Code 39, and other common barcode formats
- **PDF Processing**: Handles both text-based and image-based PDFs
- **Encrypted PDF Support**: Attempts to decrypt password-protected PDFs
- **Formatted Output**: Option to display boleto numbers with proper spacing

## Installation

### Prerequisites

- Python 3.7 or higher
- macOS, Linux, or Windows

### Setup

#### Option 1: Install as a Package (Recommended)

1. **Install from PyPI (when available):**
   ```bash
   pip install boleto-extractor
   ```

2. **Install from GitHub:**
   ```bash
   pip install git+https://github.com/pedrinho/boleto_extractor.git
   ```

3. **Install zbar (for barcode reading):**
   - **macOS:** `brew install zbar`
   - **Ubuntu/Debian:** `sudo apt-get install libzbar0`
   - **Windows:** Download from [zbar releases](https://github.com/NaturalHistoryMuseum/pyzbar/releases)

#### Option 2: Install from Source

1. **Clone or download this repository:**
   ```bash
   git clone https://github.com/pedrinho/boleto_extractor.git
   cd boleto_extractor
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package:**
   ```bash
   pip install -e .
   ```

4. **Install zbar (for barcode reading):**
   - **macOS:** `brew install zbar`
   - **Ubuntu/Debian:** `sudo apt-get install libzbar0`
   - **Windows:** Download from [zbar releases](https://github.com/NaturalHistoryMuseum/pyzbar/releases)

## Usage

### As a Library

```python
from boleto_extractor import BoletoExtractor, extract_boleto_numbers

# Method 1: Using the class
extractor = BoletoExtractor()
numbers = extractor.extract_boleto_numbers("boleto.pdf")

# Method 2: Using convenience function
numbers = extract_boleto_numbers("boleto.pdf")

# Extract from text
from boleto_extractor import find_boleto_numbers_in_text
text = "Boleto: 00193373700000001000500940144816060680935031"
numbers = find_boleto_numbers_in_text(text)

# Validate boleto numbers
from boleto_extractor import is_valid_boleto_number
is_valid = is_valid_boleto_number("00193373700000001000500940144816060680935031")
```

### Command Line Interface

#### Basic Usage

```bash
boleto-extractor path/to/boleto.pdf
```

#### Advanced Usage

```bash
# With verbose logging
boleto-extractor boleto.pdf --verbose

# With formatted output
boleto-extractor boleto.pdf --format

# Both verbose and formatted
boleto-extractor boleto.pdf --verbose --format
```

#### Examples

```bash
# Extract from a local PDF file
boleto-extractor /Users/pedro/Downloads/boleto.pdf

# Extract with formatted output
boleto-extractor boleto.pdf --format

# Extract with detailed logging
boleto-extractor boleto.pdf --verbose
```

### Legacy Script (Backward Compatibility)

```bash
python boleto_extractor.py path/to/boleto.pdf
```

## Output Examples

### Standard Output
```
Found 1 boleto number(s):
--------------------------------------------------
1. 00193373700000001000500940144816060680935031
--------------------------------------------------
```

### Formatted Output
```
Found 1 boleto number(s):
--------------------------------------------------
1. 0019 3373 7000 0000 1000 5009 4014 4816 0606 8093 5031
--------------------------------------------------
```

## Supported Boleto Formats

The script recognizes the following boleto number formats:

### 47-Digit Format (Standard)
- Example: `00193373700000001000500940144816060680935031`
- Format: `XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX X`

### 44-Digit Format (Alternative)
- Example: `23793381286000042335909000463305975620000335000`
- Format: `XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX`

### Supported Bank Codes
The script recognizes boleto numbers starting with common Brazilian bank codes:
- 001 (Banco do Brasil)
- 033 (Santander)
- 104 (Caixa Econômica Federal)
- 237 (Bradesco)
- 341 (Itaú)
- 356 (Real)
- 389 (Banco Mercantil)
- 422 (Safra)
- 633 (Banco Rendimento)
- 745 (Citibank)
- 756 (Sicoob)

## How It Works

The script uses multiple extraction methods to maximize success:

1. **Text Extraction**: Extracts text from PDF using pdfplumber and PyPDF2
2. **Pattern Matching**: Uses regex patterns to find boleto numbers in extracted text
3. **Barcode Scanning**: Converts PDF pages to images and scans for barcodes
4. **Validation**: Validates found numbers against known boleto formats

## Troubleshooting

### Common Issues

#### "No boleto numbers found"

**Possible causes:**
- PDF is encrypted/password protected
- PDF contains only images (no text)
- Boleto number is not in a recognized format
- PDF quality is too low for text extraction

**Solutions:**
1. Try installing PyMuPDF for better image processing:
   ```bash
   pip install PyMuPDF
   ```
2. Check if the PDF is password protected
3. Ensure the PDF contains readable text or clear barcode images

#### "Error extracting text from PDF"

**Possible causes:**
- PDF is corrupted
- PDF is encrypted with a password
- PDF format is not supported

**Solutions:**
1. Try opening the PDF in a PDF reader to verify it's not corrupted
2. If password protected, try to remove the password first
3. Convert the PDF to a different format if possible

#### "Error scanning barcodes"

**Possible causes:**
- zbar not installed
- Barcode image quality is too low
- Barcode format not supported

**Solutions:**
1. Install zbar library (see installation instructions)
2. Ensure the PDF has clear, high-resolution barcode images
3. Try the `--verbose` flag for more detailed error information

### Performance Tips

- For large PDFs, the script may take longer to process
- Use `--verbose` flag to see progress and identify bottlenecks
- Consider splitting large PDFs into smaller files if possible

## Testing

Run the test script to verify the installation:

```bash
python test_boleto.py
```

This will test the extractor with sample boleto numbers and validation functions.

## Dependencies

- **PyPDF2**: PDF text extraction
- **pdfplumber**: Advanced PDF text and image extraction
- **PyMuPDF**: PDF to image conversion (optional but recommended)
- **opencv-python**: Image processing
- **pyzbar**: Barcode reading
- **Pillow**: Image handling
- **numpy**: Numerical operations

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool.

## License

This project is open source and available under the MIT License.

## Disclaimer

This tool is designed for educational and legitimate business purposes. Always ensure you have the right to process the PDF files you're using with this tool. The authors are not responsible for any misuse of this software. 