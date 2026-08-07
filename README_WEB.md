# Boleto Extractor Web Application

A web interface for the Brazilian Boleto Number Extractor, allowing users to upload PDF files and extract boleto numbers through a clean, modern web interface.

## Features

- **Web Interface**: Clean, responsive design with drag-and-drop file upload
- **PDF Processing**: Supports both encrypted and non-encrypted PDF files
- **API Endpoints**: RESTful API for programmatic access
- **Real-time Feedback**: Progress indicators and success/error messages
- **Copy to Clipboard**: Easy copying of extracted boleto numbers
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices

## Quick Start

### Local Development

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python app.py
   ```

3. **Open in Browser**:
   Navigate to `http://localhost:3000`

### Production Deployment

Two deployment targets are supported from a single dependency set:

- **Render** (currently live): builds `Dockerfile.simple` and serves via gunicorn.
- **Vercel**: configured by `vercel.json` and `.python-version`. Vercel
  auto-detects the WSGI `app` object in `app.py`, so it needs no extra entrypoint
  or WSGI server.

Because every dependency is a self-contained wheel with no native system library,
the same `requirements.txt` works on both, and on any other host that runs Python.

#### Environment Variables

Set these environment variables in production:
- `SECRET_KEY`: **Required.** Signs the session cookie; the app refuses to start
  in production without it.
- `FLASK_ENV`: Set to `production` for production deployment
- `MAX_UPLOAD_MB`: Upload ceiling. Vercel rejects request bodies over 4.5MB
  before the app is reached, so keep this at 4 or below there.
- `PORT`: Port number (local only; set automatically by the platform)

## API Usage

### Endpoint: `POST /api/extract`

Extract boleto numbers from a PDF file via API.

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
  "boleto_numbers": ["1234567890123456789012345678901234567890123"],
  "formatted_numbers": ["12345.67890 12345.678901 12345.678901 1 234567890123456"],
  "count": 1
}
```

### Example API Usage (JavaScript)

```javascript
const file = document.getElementById('fileInput').files[0];
const reader = new FileReader();

reader.onload = function(e) {
    const base64 = e.target.result.split(',')[1];
    
    fetch('/api/extract', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            file: base64,
            password: 'optional_password',
            format: true
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Found boleto numbers:', data.boleto_numbers);
        } else {
            console.error('Error:', data.error);
        }
    });
};

reader.readAsDataURL(file);
```

## File Structure

```
boleto/
├── app.py                 # Flask web application
├── boleto_extractor/      # Core extraction library
├── templates/             # HTML templates
│   ├── index.html        # Main web interface
│   ├── 404.html          # Error page
│   └── 500.html          # Server error page
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Stylesheet
│   └── js/
│       └── script.js     # JavaScript functionality
├── requirements.txt      # Runtime dependencies (pinned)
├── requirements-dev.txt  # Test dependencies
├── vercel.json          # Vercel function config
├── Dockerfile.simple    # Render container image
├── .python-version      # Python version specification
├── start                # One-stop local launcher
└── README_WEB.md        # This file
```

## Technical Details

### Supported PDF Types
- Standard PDF files
- Password-protected PDF files
- Multi-page PDF documents
- PDFs with embedded images

### Extraction Methods
1. **Barcode Scanning**: Primary method using image processing
2. **Text Extraction**: Fallback method for text-based PDFs
3. **Raw Content Analysis**: For encrypted or complex PDFs

### Security Features
- File size limits (configurable via `MAX_UPLOAD_MB`, default 4MB)
- File type validation (PDF only)
- Temporary file cleanup
- Secure password handling

### Browser Compatibility
- Chrome/Chromium 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
The project follows Python PEP 8 standards and uses:
- Black for code formatting
- Flake8 for linting
- Pytest for testing

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source. See the main README.md for license information.

## Support

For issues and questions:
1. Check the API documentation above
2. Review the main README.md for core functionality
3. Open an issue on the project repository
