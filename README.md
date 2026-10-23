# Brazilian Boleto Number Extractor

🌐 **Try it online**: [https://boleto-extractor.vercel.app/](https://boleto-extractor.vercel.app/)

A Python tool to extract boleto numbers from Brazilian boleto PDF files. It reads the "linha digitável" printed on the boleto, or the 44-digit barcode when there is no readable text, and returns the linha used for payments: 47 digits for bank boletos, 48 digits for utility/tax (arrecadação) boletos such as gas, power and water bills. It also reports the amount and due date the barcode carries.

## Quick Start

```bash
./start                    # web app on http://localhost:3000
./start test               # run the test suite
./start cli boleto.pdf     # extract a number from a PDF
```

That's it — no manual setup, and nothing to install system-wide. The script creates the
`venv/` and installs dependencies on first run, then re-installs automatically whenever
`requirements.txt` changes, so you never have to remember to activate anything.

The rest of this README covers installing the package standalone, using it as a library, and the web app.

## Features

- **Two Extraction Methods**: Reads the printed linha digitável from the PDF text, and falls back to scanning the Interleaved 2 of 5 barcode for image-only PDFs
- **Check Digit Validation**: Every number is verified against all of its check digits, so misreads and unrelated digit runs are never returned
- **Automatic Conversion**: Converts 44-digit barcodes to 47-digit (bank) or 48-digit (arrecadação) "linha digitável" using the official algorithms
- **Payment Details**: Amount, due date (including the February 2025 due date factor restart) and, for utility bills, the segment
- **Encrypted PDF Support**: Opens password-protected PDFs, and says clearly when a password is needed or wrong
- **Brazilian Format Output**: Option to display boleto numbers grouped as printed on the boleto
- **Clipboard Copy**: Option to copy boleto numbers directly to clipboard for easy pasting
- **Clean Output**: No numbering or extra formatting in results

## Installation

### Prerequisites

- Python 3.12 or higher
- macOS, Linux, or Windows

No system libraries are required — every dependency ships as a self-contained wheel.

### Setup

#### Option 1: Install from GitHub (Recommended)

1. **Install from GitHub:**
   ```bash
   pip install git+https://github.com/pedrinho/boleto_extractor.git
   ```

2. **Clipboard functionality:** The clipboard copy feature requires `pyperclip` which is automatically installed with the package.

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

4. **Clipboard functionality:** The clipboard copy feature requires `pyperclip` which is automatically installed with the package.

## Usage

### As a Library

```python
from boleto_extractor import BoletoExtractor, PasswordRequired, WrongPassword

extractor = BoletoExtractor()

# Linha digitável of every boleto in the PDF
numbers = extractor.extract_boleto_numbers("boleto.pdf")

# Full details. Accepts a path or the PDF's bytes.
for boleto in extractor.extract("boleto.pdf"):
    print(boleto.linha, boleto.formatted, boleto.amount, boleto.due_date)

# Encrypted PDFs
try:
    numbers = extractor.extract_boleto_numbers("encrypted.pdf", password="mypassword")
except (PasswordRequired, WrongPassword) as e:
    print(e)

# Convert 44-digit barcode to 47-digit linha digitável
barcode = "19797116900000386000000004572849356277103564"
linha = extractor.barcode_to_linha_digitavel(barcode)

# Format output with spaces
formatted = extractor.format_boleto_number("19790000050457284935662771035649711690000038600")
# Result: "19790.00005 04572.849356 62771.035649 7 11690000038600"
```

`extract()` returns `BoletoInfo` objects with `barcode`, `linha`, `formatted`, `kind`
(`"bank"` or `"arrecadacao"`), `amount` (a `Decimal`, or `None` when the barcode leaves it
to the payer), `due_date` (bank boletos only) and `segment` (arrecadação only).

Unreadable or locked PDFs raise `InvalidPdf`, `PasswordRequired` or `WrongPassword`, all
subclasses of `PdfError`; a missing file raises `FileNotFoundError`.

### Command Line Interface

```bash
boleto-extractor path/to/boleto.pdf
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
19790.00005 04572.849356 62771.035649 7 11690000038600
--------------------------------------------------
```

### With Details
```
Found 1 boleto number(s):
--------------------------------------------------
19790000050457284935662771035649711690000038600
  Bank boleto, R$ 386,00, due 10/08/2025
--------------------------------------------------
```

### Clipboard Output
```
Found 1 boleto number(s):
--------------------------------------------------
19790000050457284935662771035649711690000038600
--------------------------------------------------
✓ Copied to clipboard: 19790000050457284935662771035649711690000038600
```

### Formatted Output with Clipboard
```
Found 1 boleto number(s):
--------------------------------------------------
19790.00005 04572.849356 62771.035649 7 11690000038600
--------------------------------------------------
✓ Copied to clipboard: 19790.00005 04572.849356 62771.035649 7 11690000038600
```

## Supported Boleto Formats

Both kinds of Brazilian boleto share a 44-digit barcode and differ in their "linha digitável" (47 digits for bank boletos, 48 for arrecadação boletos):

### 44-Digit Barcode
- **Format**: `XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX`
- **Example**: `19797116900000386000000004572849356277103564`
- **Source**: What infrared pistols/scanners read from the barcode

### 47-Digit Linha Digitável (Bank Boletos)
- **Format**: `XXXXX.XXXXX XXXXX.XXXXXX XXXXX.XXXXXX X XXXXXXXXXXXXXX`
- **Example**: `19790.00005 04572.849356 62771.035649 7 11690000038600`
- **Usage**: Standard format for payments and manual entry

### 48-Digit Linha Digitável (Arrecadação)
Utility and tax bills (gas, power, water, city taxes) use barcodes starting with `8`.
- **Format**: `XXXXXXXXXXX-X XXXXXXXXXXX-X XXXXXXXXXXX-X XXXXXXXXXXX-X`
- **Example**: `82650000001-1 23450001123-9 45678901234-5 56789012345-6`

### Conversion and Validation
Bank barcodes are converted to the 47-digit "linha digitável" using the official Modulo 10 algorithm for each field's check digit, and carry a Modulo 11 general check digit. Arrecadação barcodes are split into four 11-digit blocks, each followed by a check digit computed with Modulo 10 or Modulo 11, as selected by the barcode's third digit.

Every check digit is verified before a number is returned. Any bank's boleto is accepted; there is no list of bank codes.

### Due Dates
A bank barcode encodes its due date as a factor: days since 1997-10-07. The factor reached 9999 on 2025-02-21 and restarted at 1000 on 2025-02-22, so each factor now names two dates about 24.6 years apart; the extractor picks the one nearer to today.

## How It Works

1. **Text**: Reads the text of each page and looks for a printed linha digitável (with or without its dots, dashes and spaces). Bare 44-digit runs are ignored: invoices also print 44-digit NF-e access keys.
2. **Barcode Scanning**: If no page has a linha, renders each page and scans it for Interleaved 2 of 5 barcodes using zxing-cpp
3. **Validation**: Keeps only numbers whose check digits are all correct
4. **Conversion**: Converts 44-digit barcodes to 47-digit (bank) or 48-digit (arrecadação) "linha digitável", and decodes amount and due date

Only the first 20 pages are processed, and each page is rendered at no more than 12 million pixels, so a hostile PDF cannot exhaust memory.

## Troubleshooting

#### "No boleto numbers found"

**Possible causes:**
- PDF contains only images with low-quality barcodes
- The linha digitável is not in the PDF's text, and the barcode is damaged or cut off
- The boleto is beyond the first 20 pages

**Solutions:**
1. Ensure the PDF has a clear, high-resolution barcode
2. Try the `--verbose` flag for more detailed error information

#### "This PDF is password protected" / "The password is incorrect"

Provide the PDF's password. On the command line, run without `--password` and you will be prompted for it, which keeps it out of your shell history.

#### "This file could not be read as a PDF"

The file is corrupted or is not a PDF. Try opening it in a PDF reader.

## Usage Examples

Basic usage:
```bash
boleto-extractor boleto.pdf
```

With Brazilian format:
```bash
boleto-extractor boleto.pdf --format
```

With amount and due date:
```bash
boleto-extractor boleto.pdf --details
```

Copy to clipboard:
```bash
boleto-extractor boleto.pdf --clipboard
```

Encrypted PDFs (prompts for the password):
```bash
boleto-extractor encrypted.pdf
```

With the password on the command line (visible in shell history):
```bash
boleto-extractor encrypted.pdf --password mypassword
```

With verbose output:
```bash
boleto-extractor boleto.pdf --verbose
```

Combined options:
```bash
boleto-extractor encrypted.pdf --password mypassword --verbose --format --details --clipboard
```

## Web App

`./start` runs the web app locally at http://localhost:3000. It listens on localhost only,
because development mode runs the Werkzeug debugger; set `HOST` to change that on a
network you trust.

Uploads are processed in memory and never written to disk, logged, or stored in a cookie:
results are rendered straight into the response to the upload, and the app keeps no
session, so there is no secret key to configure.

### Deployment

Deployment is on **Vercel**, configured by `vercel.json` and `.python-version`.
Vercel auto-detects the WSGI `app` object in `app.py`, so no extra entrypoint or
WSGI server is needed, and deploys are triggered by pushing to `main`. Each request may
run for at most 30 seconds.

Because every dependency is a self-contained wheel with no native system library,
the same `requirements.txt` also runs unmodified on any other host with Python.

### Environment Variables

- `FLASK_ENV`: `production` adds an HSTS header; `development` enables the debugger locally
- `MAX_UPLOAD_MB`: Upload ceiling. Vercel rejects request bodies over 4.5MB
  before the app is reached, so keep this at 4 or below there.
- `ENABLE_PUBLIC_API`: `true` enables the JSON API below. Disabled (404) by default.
- `API_KEY`: If set, the API requires a matching `X-API-Key` header
- `HOST`, `PORT`: Where the local development server listens

### API: `POST /api/extract`

**Request Body (JSON)**:
```json
{
  "file": "base64_encoded_pdf_content",
  "password": "optional_password",
  "format": true
}
```

**Response**:
```json
{
  "success": true,
  "boleto_numbers": ["19790000050457284935662771035649711690000038600"],
  "formatted_numbers": ["19790.00005 04572.849356 62771.035649 7 11690000038600"],
  "count": 1,
  "boletos": [
    {
      "barcode": "19797116900000386000000004572849356277103564",
      "linha": "19790000050457284935662771035649711690000038600",
      "formatted": "19790.00005 04572.849356 62771.035649 7 11690000038600",
      "kind": "bank",
      "amount": "386.00",
      "due_date": "2025-08-10",
      "segment": null
    }
  ]
}
```

`formatted_numbers` is empty unless `format` is true. Errors return `"success": false`
and an `"error"` message, with status 400 for a bad request or an unreadable or locked PDF.

## Dependencies

- **PyMuPDF**: PDF text extraction and page rendering
- **zxing-cpp**: Barcode reading (Interleaved 2 of 5)
- **numpy**: Hands rendered pages to the barcode reader
- **Flask**: Web app
- **pyperclip**: Clipboard functionality (for copy to clipboard feature)

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool.

## License

This project is licensed under the GNU Affero General Public License v3.0 or later (see `LICENSE`), because PyMuPDF, which it depends on, is AGPL. If you run a modified version as a network service, you must offer its source to the service's users.

## Disclaimer

This tool is designed for educational and legitimate business purposes. Always ensure you have the right to process the PDF files you're using with this tool. The authors are not responsible for any misuse of this software. 
