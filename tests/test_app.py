#!/usr/bin/env python3
"""
Tests for the Flask web layer.

These use Flask's test client against the real fixtures - no mocking of the
extraction pipeline.
"""

import base64
import importlib
import io
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import app as app_module

FIXTURES = Path(__file__).parent / 'fixtures'
BRADESCO = FIXTURES / 'boleto_bradesco.pdf'
ENCRYPTED = FIXTURES / 'boleto_encrypted.pdf'
BRADESCO_EXPECTED = '19790000050457284935662771035649711690000038600'
BRADESCO_FORMATTED = '19790.00005 04572.849356 62771.035649 7 11690000038600'


def upload(client, path=BRADESCO, filename='boleto.pdf', **form):
    data = {'file': (io.BytesIO(Path(path).read_bytes()), filename), **form}
    return client.post('/extract', data=data, content_type='multipart/form-data')


class TestPages(unittest.TestCase):
    """Basic page rendering."""

    def setUp(self):
        app_module.app.config['TESTING'] = True
        self.client = app_module.app.test_client()

    def test_index_renders(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'uploadForm', resp.data)

    def test_index_advertises_the_real_upload_limit(self):
        """The UI must not promise a size the host will reject."""
        resp = self.client.get('/')
        expected = f"{app_module.MAX_UPLOAD_MB:g}MB".encode()
        self.assertIn(expected, resp.data)

    def test_health_check(self):
        resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['status'], 'healthy')

    def test_security_headers_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(resp.headers['X-Frame-Options'], 'DENY')
        self.assertIn('Content-Security-Policy', resp.headers)

    def test_csp_allows_only_own_scripts_and_cdn_fonts(self):
        csp = self.client.get('/').headers['Content-Security-Policy']
        directives = dict(d.strip().split(' ', 1) for d in csp.split(';'))
        self.assertEqual(directives['script-src'], "'self'")
        self.assertIn('https://cdnjs.cloudflare.com', directives['font-src'])
        self.assertNotIn('unsafe-inline', csp)

    def test_page_has_no_inline_event_handlers(self):
        """The CSP blocks them, so they would silently do nothing."""
        resp = upload(self.client)
        self.assertNotIn(b'onclick=', resp.data)
        self.assertIn(f'data-copy="{BRADESCO_EXPECTED}"'.encode(), resp.data)

    def test_unknown_route_renders_404_page(self):
        resp = self.client.get('/no-such-page')
        self.assertEqual(resp.status_code, 404)


class TestWebUpload(unittest.TestCase):
    """The browser upload flow at /extract."""

    def setUp(self):
        app_module.app.config['TESTING'] = True
        self.client = app_module.app.test_client()

    def test_upload_renders_results_directly(self):
        resp = upload(self.client)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(BRADESCO_EXPECTED.encode(), resp.data)
        self.assertIn(b'Found 1 boleto number(s)', resp.data)
        self.assertIn(b'R$ 386,00', resp.data)
        self.assertIn(b'10/08/2025', resp.data)

    def test_results_never_reach_a_cookie_or_cache(self):
        resp = upload(self.client)
        self.assertNotIn('Set-Cookie', resp.headers)
        self.assertEqual(resp.headers['Cache-Control'], 'no-store')

    def test_format_option(self):
        resp = upload(self.client, format='on')
        self.assertIn(BRADESCO_FORMATTED.encode(), resp.data)
        self.assertIn(b'name="format" checked', resp.data)

    def test_get_goes_back_to_the_form(self):
        resp = self.client.get('/extract')
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.headers['Location'].endswith('/'))

    def test_non_pdf_is_rejected(self):
        data = {'file': (io.BytesIO(b'not a pdf'), 'evil.exe')}
        resp = self.client.post('/extract', data=data, content_type='multipart/form-data')
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b'Please upload a PDF file', resp.data)

    def test_pdf_extension_with_other_content_is_rejected(self):
        data = {'file': (io.BytesIO(b'MZ\x90\x00 not a pdf'), 'fake.pdf')}
        resp = self.client.post('/extract', data=data, content_type='multipart/form-data')
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b'could not be read as a PDF', resp.data)

    def test_missing_file_is_rejected(self):
        resp = self.client.post('/extract', data={}, content_type='multipart/form-data')
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b'No file selected', resp.data)

    def test_empty_filename_is_rejected(self):
        data = {'file': (io.BytesIO(b''), '')}
        resp = self.client.post('/extract', data=data, content_type='multipart/form-data')
        self.assertIn(b'No file selected', resp.data)

    def test_password_required(self):
        resp = upload(self.client, ENCRYPTED)
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b'password protected', resp.data)

    def test_wrong_password(self):
        resp = upload(self.client, ENCRYPTED, password='wrong')
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b'password is incorrect', resp.data)

    def test_right_password(self):
        resp = upload(self.client, ENCRYPTED, password='secret')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(BRADESCO_EXPECTED.encode(), resp.data)

    def test_no_boleto_found(self):
        with patch.object(app_module.extractor, 'extract', return_value=[]):
            resp = upload(self.client)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'No boleto numbers found', resp.data)

    def test_unexpected_error_is_not_shown_to_the_user(self):
        with patch.object(app_module.extractor, 'extract', side_effect=RuntimeError('/secret/path')):
            with self.assertLogs('app', level='ERROR'):
                resp = upload(self.client)
        self.assertEqual(resp.status_code, 500)
        self.assertNotIn(b'/secret/path', resp.data)
        self.assertIn(b'Something went wrong', resp.data)

    def test_too_large(self):
        app_module.app.config['MAX_CONTENT_LENGTH'] = 1024
        try:
            resp = upload(self.client)
        finally:
            app_module.app.config['MAX_CONTENT_LENGTH'] = int(app_module.MAX_UPLOAD_MB * 1024 * 1024)
        self.assertEqual(resp.status_code, 413)
        self.assertIn(b'File too large', resp.data)


class TestApiGate(unittest.TestCase):
    """The /api/extract endpoint is disabled by default and key-gated when enabled."""

    def setUp(self):
        app_module.app.config['TESTING'] = True
        self.client = app_module.app.test_client()
        self.payload = base64.b64encode(BRADESCO.read_bytes()).decode()

    def post(self, json, env, headers=None):
        with patch.dict(os.environ, env, clear=False):
            return self.client.post('/api/extract', json=json, headers=headers or {})

    def test_api_is_404_when_disabled(self):
        resp = self.post({'file': ''}, {'ENABLE_PUBLIC_API': 'false'})
        self.assertEqual(resp.status_code, 404)

    def test_api_works_when_enabled(self):
        resp = self.post({'file': self.payload, 'format': True}, {'ENABLE_PUBLIC_API': 'true'})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body['success'])
        self.assertEqual(body['boleto_numbers'], [BRADESCO_EXPECTED])
        self.assertEqual(body['formatted_numbers'], [BRADESCO_FORMATTED])
        self.assertEqual(body['count'], 1)
        self.assertEqual(body['boletos'][0]['amount'], '386.00')
        self.assertEqual(body['boletos'][0]['kind'], 'bank')
        self.assertEqual(resp.headers['Cache-Control'], 'no-store')

    def test_api_rejects_wrong_key(self):
        env = {'ENABLE_PUBLIC_API': 'true', 'API_KEY': 'correct-key'}
        resp = self.post({'file': ''}, env, {'X-API-Key': 'wrong-key'})
        self.assertEqual(resp.status_code, 403)

    def test_api_rejects_missing_key(self):
        env = {'ENABLE_PUBLIC_API': 'true', 'API_KEY': 'correct-key'}
        resp = self.post({'file': ''}, env)
        self.assertEqual(resp.status_code, 403)

    def test_api_accepts_correct_key(self):
        env = {'ENABLE_PUBLIC_API': 'true', 'API_KEY': 'correct-key'}
        resp = self.post({'file': self.payload}, env, {'X-API-Key': 'correct-key'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['boleto_numbers'], [BRADESCO_EXPECTED])

    def test_api_rejects_bad_base64(self):
        resp = self.post({'file': '!!!not-base64!!!'}, {'ENABLE_PUBLIC_API': 'true'})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()['error'], 'Invalid file encoding')

    def test_api_rejects_missing_or_non_json_body(self):
        env = {'ENABLE_PUBLIC_API': 'true'}
        self.assertEqual(self.post({}, env).status_code, 400)
        with patch.dict(os.environ, env, clear=False):
            resp = self.client.post('/api/extract', data='file=x', content_type='text/plain')
        self.assertEqual(resp.status_code, 400)

    def test_api_reports_pdf_errors(self):
        env = {'ENABLE_PUBLIC_API': 'true'}
        encrypted = base64.b64encode(ENCRYPTED.read_bytes()).decode()
        resp = self.post({'file': encrypted, 'password': 'wrong'}, env)
        self.assertEqual(resp.status_code, 400)
        self.assertIn('incorrect', resp.get_json()['error'])

        resp = self.post({'file': base64.b64encode(b'not a pdf').decode()}, env)
        self.assertEqual(resp.status_code, 400)

    def test_api_rejects_non_string_password(self):
        resp = self.post({'file': self.payload, 'password': 123}, {'ENABLE_PUBLIC_API': 'true'})
        self.assertEqual(resp.status_code, 400)

    def test_api_hides_unexpected_errors(self):
        with patch.object(app_module.extractor, 'extract', side_effect=RuntimeError('/secret/path')):
            with self.assertLogs('app', level='ERROR'):
                resp = self.post({'file': self.payload}, {'ENABLE_PUBLIC_API': 'true'})
        self.assertEqual(resp.status_code, 500)
        self.assertNotIn('/secret/path', resp.get_data(as_text=True))


class TestConfig(unittest.TestCase):

    def tearDown(self):
        importlib.reload(app_module)

    def test_upload_limit_is_configurable(self):
        with patch.dict(os.environ, {'MAX_UPLOAD_MB': '2'}, clear=False):
            mod = importlib.reload(app_module)
            self.assertEqual(mod.app.config['MAX_CONTENT_LENGTH'], 2 * 1024 * 1024)

    def test_no_secret_key_is_needed(self):
        """Nothing uses the session, so the app must not depend on a secret."""
        with patch.dict(os.environ, {'FLASK_ENV': 'production'}, clear=False):
            os.environ.pop('SECRET_KEY', None)
            mod = importlib.reload(app_module)
        self.assertIsNone(mod.app.config['SECRET_KEY'])
        mod.app.config['TESTING'] = True
        resp = upload(mod.app.test_client())
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Strict-Transport-Security', resp.headers)


if __name__ == '__main__':
    unittest.main()
