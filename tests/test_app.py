#!/usr/bin/env python3
"""
Tests for the Flask web layer.

app.py had no tests at all and was excluded from coverage measurement, so the
upload flow and the API key gate were entirely unverified. These use Flask's
test client against the real fixtures - no mocking of the extraction pipeline.
"""

import importlib
import io
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import app as app_module

FIXTURES = Path(__file__).parent / 'fixtures'
BRADESCO = FIXTURES / 'boleto_bradesco.pdf'
BRADESCO_EXPECTED = '19790000050457284935662771035649711690000038600'


def reload_app(**env):
    """Reimport app.py under a given environment, returning the fresh module."""
    with patch.dict(os.environ, env, clear=False):
        return importlib.reload(app_module)


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

    def test_unknown_route_renders_404_page(self):
        resp = self.client.get('/no-such-page')
        self.assertEqual(resp.status_code, 404)


class TestWebUpload(unittest.TestCase):
    """The browser upload flow at /extract."""

    def setUp(self):
        app_module.app.config['TESTING'] = True
        self.client = app_module.app.test_client()

    def test_upload_extracts_number(self):
        with open(BRADESCO, 'rb') as fh:
            data = {'file': (io.BytesIO(fh.read()), 'boleto.pdf')}
            resp = self.client.post('/extract', data=data,
                                    content_type='multipart/form-data',
                                    follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        with self.client.session_transaction() as sess:
            results = sess.get('results')
        self.assertIsNotNone(results, "extraction results were not stored in the session")
        self.assertIn(BRADESCO_EXPECTED, [r['raw'] for r in results])

    def test_non_pdf_is_rejected(self):
        data = {'file': (io.BytesIO(b'not a pdf'), 'evil.exe')}
        resp = self.client.post('/extract', data=data,
                                content_type='multipart/form-data',
                                follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Please upload a PDF file', resp.data)

    def test_missing_file_is_rejected(self):
        resp = self.client.post('/extract', data={},
                                content_type='multipart/form-data',
                                follow_redirects=True)
        self.assertIn(b'No file selected', resp.data)

    def test_empty_filename_is_rejected(self):
        data = {'file': (io.BytesIO(b''), '')}
        resp = self.client.post('/extract', data=data,
                                content_type='multipart/form-data',
                                follow_redirects=True)
        self.assertIn(b'No file selected', resp.data)


class TestApiGate(unittest.TestCase):
    """The /api/extract endpoint is disabled by default and key-gated when enabled."""

    def _client(self, **env):
        mod = reload_app(**env)
        mod.app.config['TESTING'] = True
        return mod, mod.app.test_client()

    def tearDown(self):
        importlib.reload(app_module)  # restore default env for other tests

    def test_api_is_404_when_disabled(self):
        with patch.dict(os.environ, {'ENABLE_PUBLIC_API': 'false'}, clear=False):
            client = app_module.app.test_client()
            resp = client.post('/api/extract', json={'file': ''})
            self.assertEqual(resp.status_code, 404)

    def test_api_works_when_enabled(self):
        with patch.dict(os.environ, {'ENABLE_PUBLIC_API': 'true'}, clear=False):
            client = app_module.app.test_client()
            import base64
            payload = base64.b64encode(BRADESCO.read_bytes()).decode()
            resp = client.post('/api/extract', json={'file': payload})
            self.assertEqual(resp.status_code, 200)
            body = resp.get_json()
            self.assertTrue(body['success'])
            self.assertIn(BRADESCO_EXPECTED, body['boleto_numbers'])

    def test_api_rejects_wrong_key(self):
        env = {'ENABLE_PUBLIC_API': 'true', 'API_KEY': 'correct-key'}
        with patch.dict(os.environ, env, clear=False):
            client = app_module.app.test_client()
            resp = client.post('/api/extract', json={'file': ''},
                               headers={'X-API-Key': 'wrong-key'})
            self.assertEqual(resp.status_code, 403)

    def test_api_rejects_missing_key(self):
        env = {'ENABLE_PUBLIC_API': 'true', 'API_KEY': 'correct-key'}
        with patch.dict(os.environ, env, clear=False):
            client = app_module.app.test_client()
            resp = client.post('/api/extract', json={'file': ''})
            self.assertEqual(resp.status_code, 403)

    def test_api_accepts_correct_key(self):
        """The right key gets past the gate; an empty payload then yields no results."""
        env = {'ENABLE_PUBLIC_API': 'true', 'API_KEY': 'correct-key'}
        with patch.dict(os.environ, env, clear=False):
            client = app_module.app.test_client()
            resp = client.post('/api/extract', json={'file': ''},
                               headers={'X-API-Key': 'correct-key'})
            self.assertNotEqual(resp.status_code, 403)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_json()['boleto_numbers'], [])

    def test_api_rejects_bad_base64(self):
        with patch.dict(os.environ, {'ENABLE_PUBLIC_API': 'true'}, clear=False):
            client = app_module.app.test_client()
            resp = client.post('/api/extract', json={'file': '!!!not-base64!!!'})
            self.assertEqual(resp.status_code, 400)


class TestProductionConfig(unittest.TestCase):
    """Production must not fall back to the public repo's dev secret."""

    def tearDown(self):
        importlib.reload(app_module)

    def test_missing_secret_key_in_production_raises(self):
        env = {'FLASK_ENV': 'production'}
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop('SECRET_KEY', None)
            with self.assertRaises(RuntimeError) as ctx:
                importlib.reload(app_module)
            self.assertIn('SECRET_KEY', str(ctx.exception))

    def test_production_with_secret_key_starts(self):
        env = {'FLASK_ENV': 'production', 'SECRET_KEY': 'a-real-secret'}
        with patch.dict(os.environ, env, clear=False):
            mod = importlib.reload(app_module)
            self.assertEqual(mod.app.config['SECRET_KEY'], 'a-real-secret')
            self.assertTrue(mod.app.config['SESSION_COOKIE_SECURE'])

    def test_upload_limit_is_configurable(self):
        with patch.dict(os.environ, {'MAX_UPLOAD_MB': '2'}, clear=False):
            mod = importlib.reload(app_module)
            self.assertEqual(mod.app.config['MAX_CONTENT_LENGTH'], 2 * 1024 * 1024)


if __name__ == '__main__':
    unittest.main()
