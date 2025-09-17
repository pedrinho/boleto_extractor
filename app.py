#!/usr/bin/env python3
"""
Flask Web Application for Brazilian Boleto Number Extractor

This module provides a web interface and API endpoints for extracting
boleto numbers from Brazilian boleto PDF files.
"""

import os
import tempfile
import logging
from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, abort
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from boleto_extractor.extractor import BoletoExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
def is_api_enabled() -> bool:
    """Return True if public API is enabled via env var."""
    return os.environ.get('ENABLE_PUBLIC_API', 'false').lower() == 'true'

def require_api_key_if_set():
    """If API_KEY is set, require matching X-API-Key header; else no-op."""
    expected = os.environ.get('API_KEY')
    if expected:
        provided = request.headers.get('X-API-Key')
        if not provided or provided != expected:
            abort(403)

@app.after_request
def add_security_headers(response):
    """Add basic security headers to all responses."""
    # Only send HSTS in production over HTTPS
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    # Lock down content sources to our own origin and approved CDNs used in templates
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' https://cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "object-src 'none'; frame-ancestors 'none'"
    )
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the main page with the upload form."""
    return render_template('index.html')

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
        "error": "error_message"
    }
    """
    # Protect API: disabled by default unless ENABLE_PUBLIC_API=true
    if not is_api_enabled():
        abort(404)

    # If API_KEY is defined, require correct X-API-Key header
    require_api_key_if_set()

    try:
        data = request.get_json()
        
        if not data or 'file' not in data:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        # Get optional parameters
        password = data.get('password', '')
        format_output = data.get('format', False)
        
        # Decode base64 file content
        import base64
        try:
            file_content = base64.b64decode(data['file'])
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Invalid file encoding: {str(e)}'
            }), 400
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Extract boleto numbers
            extractor = BoletoExtractor()
            boleto_numbers = extractor.extract_boleto_numbers(temp_file_path, password)
            
            if not boleto_numbers:
                return jsonify({
                    'success': True,
                    'boleto_numbers': [],
                    'formatted_numbers': [],
                    'message': 'No boleto numbers found in the PDF'
                })
            
            # Format numbers if requested
            formatted_numbers = []
            if format_output:
                formatted_numbers = [extractor.format_boleto_number(num) for num in boleto_numbers]
            
            return jsonify({
                'success': True,
                'boleto_numbers': boleto_numbers,
                'formatted_numbers': formatted_numbers,
                'count': len(boleto_numbers)
            })
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
                
    except Exception as e:
        logger.error(f"Error in extract_boleto_api: {e}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/extract', methods=['POST'])
def extract_boleto_web():
    """
    Web endpoint to extract boleto numbers from uploaded PDF file.
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        password = request.form.get('password', '')
        format_output = request.form.get('format') == 'on'
        
        # Check if file was actually selected
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        # Validate file type
        if not allowed_file(file.filename):
            flash('Please upload a PDF file', 'error')
            return redirect(request.url)
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Extract boleto numbers
            extractor = BoletoExtractor()
            boleto_numbers = extractor.extract_boleto_numbers(temp_file_path, password if password else None)
            
            if not boleto_numbers:
                flash('No boleto numbers found in the PDF', 'info')
            else:
                # Store results in session for display
                results = []
                for num in boleto_numbers:
                    result = {
                        'raw': num,
                        'formatted': extractor.format_boleto_number(num) if format_output else num
                    }
                    results.append(result)
                
                flash(f'Found {len(boleto_numbers)} boleto number(s)', 'success')
                # Store results in session
                from flask import session
                session['results'] = results
                session['format_output'] = format_output
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
        
        return redirect(url_for('index'))
        
    except RequestEntityTooLarge:
        flash('File too large. Maximum size is 16MB.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in extract_boleto_web: {e}")
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/health')
def health_check():
    """Health check endpoint for deployment."""
    return jsonify({'status': 'healthy', 'service': 'boleto-extractor'})

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    flash('File too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    
    # Run the app
    port = int(os.environ.get('PORT', 3000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
