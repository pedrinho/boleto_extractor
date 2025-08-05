# Brazilian Boleto Number Extractor

A Python tool to extract boleto numbers from Brazilian boleto PDF files. This tool reads 44-digit barcodes from PDFs and converts them to the standard 47-digit "linha digitável" format used for payments.

## Features

- **Barcode-Focused Extraction**: Primarily reads 44-digit barcodes from PDFs
- **Automatic Conversion**: Converts 44-digit barcodes to 47-digit "linha digitável" using official algorithms
- **Multiple Extraction Methods**: Barcode scanning, text extraction, and raw PDF content analysis
- **Barcode Detection**: Reads Interleaved 2 of 5 (I25) and other common barcode formats
- **PDF Processing**: Handles both text-based and image-based PDFs
- **Encrypted PDF Support**: Attempts to decrypt password-protected PDFs
- **Formatted Output**: Option to display boleto numbers with proper spacing
- **Clean Output**: No numbering or extra formatting in results

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
from boleto_extractor import BoletoExtractor

# Create extractor and extract boleto numbers
extractor = BoletoExtractor()
numbers = extractor.extract_boleto_numbers("boleto.pdf")

# Extract from encrypted PDF
numbers = extractor.extract_boleto_numbers("encrypted.pdf", password="mypassword")

# Convert 44-digit barcode to 47-digit linha digitável
barcode = "19797116900000386000000004572849356277103564"
linha = extractor.barcode_to_linha_digitavel(barcode)

# Format output with spaces
formatted = extractor.format_boleto_number("19790000050457284935662771035649711690000038600")
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

# Extract from encrypted PDF
boleto-extractor encrypted.pdf --password mypassword

# Extract from encrypted PDF with all options
boleto-extractor encrypted.pdf --password mypassword --verbose --format
```

#### Examples

```bash
# Extract from a local PDF file
boleto-extractor /Users/pedro/Downloads/boleto.pdf

# Extract with formatted output
boleto-extractor boleto.pdf --format

# Extract with detailed logging
boleto-extractor boleto.pdf --verbose

# Extract from encrypted PDF
boleto-extractor encrypted.pdf --password mypassword

# Extract from encrypted PDF with all options
boleto-extractor encrypted.pdf --password mypassword --verbose --format
```

## Output Examples

### Standard Output
```
Found 1 boleto number(s):
--------------------------------------------------
19790000050457284935662771035649711690000038600
--------------------------------------------------
```

### Formatted Output
```
Found 1 boleto number(s):
--------------------------------------------------
1979 0000 0504 5728 4935 6627 7103 5649 7116 9000 0038 600
--------------------------------------------------
```

## Supported Boleto Formats

The tool focuses on extracting 44-digit barcodes and converting them to 47-digit "linha digitável":

### 44-Digit Barcode (Input)
- **Format**: `XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX`
- **Example**: `19797116900000386000000004572849356277103564`
- **Source**: What infrared pistols/scanners read from the barcode

### 47-Digit Linha Digitável (Output)
- **Format**: `XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXX`
- **Example**: `19790000050457284935662771035649711690000038600`
- **Usage**: Standard format for payments and manual entry

### Conversion Process
The tool automatically converts 44-digit barcodes to 47-digit "linha digitável" using the official Modulo 10 algorithm for check digit calculation.

### Supported Bank Codes
The tool recognizes boleto numbers starting with common Brazilian bank codes:
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
- 197 (Banco Bradesco BBI)

## How It Works

The tool uses a barcode-focused approach to extract boleto numbers:

1. **Barcode Scanning**: Converts PDF pages to images and scans for barcodes using pyzbar
2. **Text Extraction**: As backup, extracts text from PDF and looks for 44-digit barcode patterns
3. **Raw Content Analysis**: For encrypted PDFs, analyzes raw PDF content for barcode patterns
4. **Validation**: Validates found numbers against known Brazilian bank codes
5. **Conversion**: Converts 44-digit barcodes to 47-digit "linha digitável" using Modulo 10 algorithm
6. **Output**: Returns clean 47-digit numbers ready for payment processing

## Troubleshooting

### Common Issues

#### "No boleto numbers found"

**Possible causes:**
- PDF is encrypted/password protected
- PDF contains only images with low-quality barcodes
- Barcode is not in a recognized format
- PDF quality is too low for barcode scanning

**Solutions:**
1. Try installing PyMuPDF for better image processing:
   ```bash
   pip install PyMuPDF
   ```
2. Check if the PDF is password protected and provide the password
3. Ensure the PDF has clear, high-resolution barcode images
4. Try the `--verbose` flag for more detailed error information

#### "Error extracting text from PDF"

**Possible causes:**
- PDF is corrupted
- PDF is encrypted with a password
- PDF format is not supported

**Solutions:**
1. Try opening the PDF in a PDF reader to verify it's not corrupted
2. If password protected, provide the correct password
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

- For large PDFs, the tool may take longer to process
- Use `--verbose` flag to see progress and identify bottlenecks
- Consider splitting large PDFs into smaller files if possible

## Usage Examples

Basic usage:
```bash
boleto-extractor boleto.pdf
```

With formatting:
```bash
boleto-extractor boleto.pdf --format
```

With password for encrypted PDFs:
```bash
boleto-extractor encrypted.pdf --password mypassword
```

With verbose output:
```bash
boleto-extractor boleto.pdf --verbose
```

Combined options:
```bash
boleto-extractor encrypted.pdf --password mypassword --verbose --format
```

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