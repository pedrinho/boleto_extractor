#!/usr/bin/env python3
"""
Unit tests for CLI module.

The CLI runs against the real fixtures; only the terminal (password prompt,
clipboard) is mocked.
"""

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from boleto_extractor.cli import main

FIXTURES = Path(__file__).parent / 'fixtures'
BRADESCO = str(FIXTURES / 'boleto_bradesco.pdf')
ARRECADACAO = str(FIXTURES / 'boleto_arrecadacao.pdf')
ENCRYPTED = str(FIXTURES / 'boleto_encrypted.pdf')
BRADESCO_EXPECTED = '19790000050457284935662771035649711690000038600'
BRADESCO_FORMATTED = '19790.00005 04572.849356 62771.035649 7 11690000038600'


def run_cli(*args):
    """Run the CLI with `args`, returning (stdout, exit code)."""
    out = io.StringIO()
    code = 0
    with patch('sys.argv', ['boleto-extractor', *args]), redirect_stdout(out):
        try:
            main()
        except SystemExit as e:
            code = e.code
    return out.getvalue(), code


class TestCLI(unittest.TestCase):
    """Test cases for CLI module."""

    def test_cli_basic_usage(self):
        out, code = run_cli(BRADESCO)
        self.assertEqual(code, 0)
        self.assertIn('Found 1 boleto number(s):', out)
        self.assertIn(BRADESCO_EXPECTED, out)

    def test_cli_with_format(self):
        out, _ = run_cli(BRADESCO, '--format')
        self.assertIn(BRADESCO_FORMATTED, out)

    def test_cli_with_details(self):
        out, _ = run_cli(BRADESCO, '--details')
        self.assertIn('Bank boleto, R$ 386,00, due', out)

        out, _ = run_cli(ARRECADACAO, '-d')
        self.assertIn('Utility/tax bill, Water and sanitation, R$ 123,45', out)

    @patch('boleto_extractor.cli.CLIPBOARD_AVAILABLE', True)
    @patch('boleto_extractor.cli.pyperclip')
    def test_cli_with_clipboard(self, mock_pyperclip):
        out, _ = run_cli(BRADESCO, '--clipboard')
        mock_pyperclip.copy.assert_called_once_with(BRADESCO_EXPECTED)
        self.assertIn('Copied to clipboard', out)

    @patch('boleto_extractor.cli.CLIPBOARD_AVAILABLE', True)
    @patch('boleto_extractor.cli.pyperclip')
    def test_cli_with_format_and_clipboard(self, mock_pyperclip):
        run_cli(BRADESCO, '--format', '--clipboard')
        mock_pyperclip.copy.assert_called_once_with(BRADESCO_FORMATTED)

    @patch('boleto_extractor.cli.CLIPBOARD_AVAILABLE', False)
    def test_cli_clipboard_not_available(self):
        with self.assertLogs(level='WARNING'):
            run_cli(BRADESCO, '--clipboard')

    @patch('boleto_extractor.cli.CLIPBOARD_AVAILABLE', True)
    @patch('boleto_extractor.cli.pyperclip')
    def test_cli_clipboard_error(self, mock_pyperclip):
        mock_pyperclip.copy.side_effect = Exception("Clipboard error")
        with self.assertLogs(level='ERROR'):
            out, code = run_cli(BRADESCO, '--clipboard')
        self.assertEqual(code, 0)
        self.assertIn(BRADESCO_EXPECTED, out)

    def test_cli_with_password(self):
        out, code = run_cli(ENCRYPTED, '--password', 'secret')
        self.assertEqual(code, 0)
        self.assertIn(BRADESCO_EXPECTED, out)

    def test_cli_wrong_password(self):
        with self.assertLogs(level='ERROR') as logs:
            _, code = run_cli(ENCRYPTED, '--password', 'wrong')
        self.assertEqual(code, 1)
        self.assertIn('incorrect', logs.output[0])

    @patch('boleto_extractor.cli.getpass.getpass', return_value='secret')
    @patch('sys.stdin.isatty', return_value=True)
    def test_cli_prompts_for_password_on_a_terminal(self, _isatty, mock_getpass):
        out, code = run_cli(ENCRYPTED)
        mock_getpass.assert_called_once()
        self.assertEqual(code, 0)
        self.assertIn(BRADESCO_EXPECTED, out)

    @patch('boleto_extractor.cli.getpass.getpass')
    @patch('sys.stdin.isatty', return_value=False)
    def test_cli_does_not_prompt_without_a_terminal(self, _isatty, mock_getpass):
        with self.assertLogs(level='ERROR') as logs:
            _, code = run_cli(ENCRYPTED)
        mock_getpass.assert_not_called()
        self.assertEqual(code, 1)
        self.assertIn('password protected', logs.output[0])

    def test_cli_file_not_found(self):
        with self.assertLogs(level='ERROR'):
            _, code = run_cli(str(FIXTURES / 'nonexistent.pdf'))
        self.assertEqual(code, 1)

    def test_cli_not_pdf_file(self):
        with self.assertLogs(level='ERROR'):
            _, code = run_cli(str(FIXTURES / 'generate_fixtures.py'))
        self.assertEqual(code, 1)

    def test_cli_no_boleto_numbers_found(self):
        with patch('boleto_extractor.cli.BoletoExtractor.extract', return_value=[]):
            out, code = run_cli(BRADESCO)
        self.assertEqual(code, 0)
        self.assertIn('No boleto numbers found.', out)

    def test_cli_extraction_error(self):
        with patch('boleto_extractor.cli.BoletoExtractor.extract', side_effect=Exception("Test error")):
            with self.assertLogs(level='ERROR'):
                _, code = run_cli(BRADESCO)
        self.assertEqual(code, 1)

    def test_cli_with_verbose(self):
        with patch('boleto_extractor.cli.logging') as mock_logging:
            run_cli(BRADESCO, '--verbose')
        mock_logging.getLogger.return_value.setLevel.assert_called_with(mock_logging.DEBUG)


if __name__ == '__main__':
    unittest.main()
