#!/usr/bin/env python3
"""
Flask Web Application for Brazilian Boleto Number Extractor

This module provides a web interface and API endpoints for extracting
boleto numbers from Brazilian boleto PDF files.

Uploads are processed in memory and never written to disk, logged, or put in a
cookie. The app keeps no session at all - results are rendered straight into the
response to the upload - so there is no secret key to configure or leak.
"""

import base64
import binascii
import hmac
import logging
import os

from flask import Flask, request, jsonify, render_template, redirect, url_for, abort

from boleto_extractor import BoletoExtractor, PdfError
from boleto_extractor.barcode import format_brl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IS_PRODUCTION = os.environ.get('FLASK_ENV') == 'production'

# Upload ceiling. Keep this at or below the host's request body limit: Vercel
# rejects bodies over 4.5MB itself, before Flask is reached, so anything larger
# surfaces as an opaque platform 413 instead of the friendly handler below.
MAX_UPLOAD_MB = float(os.environ.get('MAX_UPLOAD_MB', '4'))

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = int(MAX_UPLOAD_MB * 1024 * 1024)

extractor = BoletoExtractor()

GENERIC_ERROR = 'Something went wrong while processing the file. Please try again.'

# Scripts load from our own origin only. Font Awesome's stylesheet and webfonts
# come from cdnjs, Inter from Google Fonts. No inline script or style is allowed,
# so nothing injected into a page can run.
CONTENT_SECURITY_POLICY = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' https://fonts.googleapis.com https://cdnjs.cloudflare.com",
    "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com",
    "img-src 'self' data:",
    "object-src 'none'",
    "base-uri 'none'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])

# Responses that carry boleto numbers. Nothing in between may keep a copy.
NO_STORE_ENDPOINTS = {'extract_boleto_web', 'extract_boleto_api'}


def is_api_enabled() -> bool:
    """Return True if public API is enabled via env var."""
    return os.environ.get('ENABLE_PUBLIC_API', 'false').lower() == 'true'

def require_api_key_if_set():
    """If API_KEY is set, require matching X-API-Key header; else no-op."""
    expected = os.environ.get('API_KEY')
    if expected:
        provided = request.headers.get('X-API-Key', '')
        if not hmac.compare_digest(provided.encode(), expected.encode()):
            abort(403)

@app.after_request
def add_security_headers(response):
    """Add basic security headers to all responses."""
    # Only send HSTS in production over HTTPS
    if IS_PRODUCTION:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers['Content-Security-Policy'] = CONTENT_SECURITY_POLICY
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    if request.endpoint in NO_STORE_ENDPOINTS:
        response.headers['Cache-Control'] = 'no-store'
    return response

@app.template_filter('brl')
def brl_filter(amount):
    return format_brl(amount)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def render_page(status=200, **context):
    """Render the upload page, with results or a message if given."""
    return render_template('index.html', max_upload_mb=f'{MAX_UPLOAD_MB:g}', **context), status

@app.route('/')
def index():
    """Render the main page with the upload form."""
    return render_page()

@app.route('/api/extract', methods=['POST'])
def extract_boleto_api():
    """
    API endpoint to extract boleto numbers from uploaded PDF.

    Expected JSON payload:
    {
        "file": <base64_encoded_pdf_content>,
        "password": "optional_password",
        "format": true/false
    }

    Returns:
    {
        "success": true/false,
        "boleto_numbers": ["number1", "number2"],
        "formatted_numbers": ["formatted1", "formatted2"],
        "count": 2,
        "boletos": [{"linha", "formatted", "barcode", "kind", "amount", "due_date", "segment"}],
        "error": "error_message"
    }
    """
    # Protect API: disabled by default unless ENABLE_PUBLIC_API=true
    if not is_api_enabled():
        abort(404)

    # If API_KEY is defined, require correct X-API-Key header
    require_api_key_if_set()

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or 'file' not in data:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    password = data.get('password') or None
    if password is not None and not isinstance(password, str):
        return jsonify({'success': False, 'error': 'Password must be a string'}), 400
    format_output = bool(data.get('format', False))

    try:
        file_content = base64.b64decode(data['file'], validate=True)
    except (binascii.Error, TypeError, ValueError):
        return jsonify({'success': False, 'error': 'Invalid file encoding'}), 400

    try:
        boletos = extractor.extract(file_content, password)
    except PdfError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception:
        logger.exception("Extraction failed in extract_boleto_api")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

    body = {
        'success': True,
        'boleto_numbers': [b.linha for b in boletos],
        'formatted_numbers': [b.formatted for b in boletos] if format_output else [],
        'count': len(boletos),
        'boletos': [b.as_dict() for b in boletos],
    }
    if not boletos:
        body['message'] = 'No boleto numbers found in the PDF'
    return jsonify(body)

@app.route('/extract', methods=['GET', 'POST'])
def extract_boleto_web():
    """
    Web endpoint to extract boleto numbers from uploaded PDF file.

    The results are rendered into this response rather than stored for a redirect,
    so they never leave the server in a cookie. GET is the results page being
    reloaded or bookmarked; it goes back to the form.
    """
    if request.method == 'GET':
        return redirect(url_for('index'))

    file = request.files.get('file')
    if file is None or file.filename == '':
        return render_page(400, error='No file selected')

    if not allowed_file(file.filename):
        return render_page(400, error='Please upload a PDF file')

    password = request.form.get('password') or None
    format_output = request.form.get('format') == 'on'

    try:
        boletos = extractor.extract(file.read(), password)
    except PdfError as e:
        return render_page(400, error=str(e), format_output=format_output)
    except Exception:
        logger.exception("Extraction failed in extract_boleto_web")
        return render_page(500, error=GENERIC_ERROR, format_output=format_output)

    if not boletos:
        return render_page(notice='No boleto numbers found in the PDF', format_output=format_output)
    return render_page(results=boletos, format_output=format_output)

@app.route('/health')
def health_check():
    """Health check endpoint for deployment."""
    return jsonify({'status': 'healthy', 'service': 'boleto-extractor'})

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    message = f'File too large. Maximum size is {MAX_UPLOAD_MB:g}MB.'
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': message}), 413
    return render_page(413, error=message)

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Development server only. Listens on localhost unless HOST says otherwise:
    # in development mode it runs the Werkzeug debugger, which executes code for
    # anyone who can reach it.
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 3000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    app.run(host=host, port=port, debug=debug)
