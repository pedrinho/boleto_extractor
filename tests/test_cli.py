#!/usr/bin/env python3
"""
Unit tests for CLI module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

from boleto_extractor.cli import main


class TestCLI(unittest.TestCase):
    """Test cases for CLI module."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_args = ['boleto-extractor', 'test.pdf']

    @patch('boleto_extractor.cli.BoletoExtractor')
    @patch('boleto_extractor.cli.Path')
    @patch('sys.argv', ['boleto-extractor', 'test.pdf'])
    @patch('sys.exit')
    def test_cli_basic_usage(self, mock_exit, mock_path, mock_extractor_class):
        """Test basic CLI usage."""
        # Mock Path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = '.pdf'
        mock_path_instance.__str__ = Mock(return_value='test.pdf')  # Fix string conversion
        mock_path.return_value = mock_path_instance
        
        # Mock BoletoExtractor
        mock_extractor = Mock()
        mock_extractor.extract_boleto_numbers.return_value = ['19790000050457284935662771035649711690000038600']
        mock_extractor_class.return_value = mock_extractor
        
        # Mock print to capture output
        with patch('builtins.print') as mock_print:
            main()
            
            # Verify extractor was called
            mock_extractor.extract_boleto_numbers.assert_called_once()
            # Check that it was called with the correct arguments
            call_args = mock_extractor.extract_boleto_numbers.call_args
            self.assertEqual(str(call_args[0][0]), 'test.pdf')
            self.assertEqual(call_args[0][1], None)
            
            # Verify output was printed
            mock_print.assert_called()

    @patch('boleto_extractor.cli.BoletoExtractor')
    @patch('boleto_extractor.cli.Path')
    @patch('sys.argv', ['boleto-extractor', 'test.pdf', '--format'])
    @patch('sys.exit')
    def test_cli_with_format(self, mock_exit, mock_path, mock_extractor_class):
        """Test CLI with format option."""
        # Mock Path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = '.pdf'
        mock_path_instance.__str__ = Mock(return_value='test.pdf')
        mock_path.return_value = mock_path_instance
        
        # Mock BoletoExtractor
        mock_extractor = Mock()
        mock_extractor.extract_boleto_numbers.return_value = ['19790000050457284935662771035649711690000038600']
        mock_extractor.format_boleto_number.return_value = '19790.00005 04572.849356 62771.035649 7 11690000038600'
        mock_extractor_class.return_value = mock_extractor
        
        # Mock print to capture output
        with patch('builtins.print') as mock_print:
            main()
            
            # Verify format_boleto_number was called
            mock_extractor.format_boleto_number.assert_called_once()

    @patch('boleto_extractor.cli.BoletoExtractor')
    @patch('boleto_extractor.cli.Path')
    @patch('boleto_extractor.cli.CLIPBOARD_AVAILABLE', True)
    @patch('boleto_extractor.cli.pyperclip')
    @patch('sys.argv', ['boleto-extractor', 'test.pdf', '--clipboard'])
    @patch('sys.exit')
    def test_cli_with_clipboard(self, mock_exit, mock_pyperclip, mock_path, mock_extractor_class):
        """Test CLI with clipboard option."""
        # Mock Path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = '.pdf'
        mock_path_instance.__str__ = Mock(return_value='test.pdf')
        mock_path.return_value = mock_path_instance
        
        # Mock BoletoExtractor
        mock_extractor = Mock()
        mock_extractor.extract_boleto_numbers.return_value = ['19790000050457284935662771035649711690000038600']
        mock_extractor_class.return_value = mock_extractor
        
        # Mock print to capture output
        with patch('builtins.print') as mock_print:
            main()
            
            # Verify pyperclip.copy was called
            mock_pyperclip.copy.assert_called_once()

    @patch('boleto_extractor.cli.BoletoExtractor')
    @patch('boleto_extractor.cli.Path')
    @patch('boleto_extractor.cli.CLIPBOARD_AVAILABLE', True)
    @patch('boleto_extractor.cli.pyperclip')
    @patch('sys.argv', ['boleto-extractor', 'test.pdf', '--format', '--clipboard'])
    @patch('sys.exit')
    def test_cli_with_format_and_clipboard(self, mock_exit, mock_pyperclip, mock_path, mock_extractor_class):
        """Test CLI with format and clipboard options."""
        # Mock Path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = '.pdf'
        mock_path_instance.__str__ = Mock(return_value='test.pdf')
        mock_path.return_value = mock_path_instance
        
        # Mock BoletoExtractor
        mock_extractor = Mock()
        mock_extractor.extract_boleto_numbers.return_value = ['19790000050457284935662771035649711690000038600']
        mock_extractor.format_boleto_number.return_value = '19790.00005 04572.849356 62771.035649 7 11690000038600'
        mock_extractor_class.return_value = mock_extractor
        
        # Mock print to capture output
        with patch('builtins.print') as mock_print:
            main()
            
            # Verify both format and clipboard were used
            # format_boleto_number is called twice: once for display, once for clipboard
            self.assertEqual(mock_extractor.format_boleto_number.call_count, 2)
            mock_pyperclip.copy.assert_called_once()

    @patch('boleto_extractor.cli.BoletoExtractor')
    @patch('boleto_extractor.cli.Path')
    @patch('sys.argv', ['boleto-extractor', 'test.pdf', '--password', 'mypassword'])
    @patch('sys.exit')
    def test_cli_with_password(self, mock_exit, mock_path, mock_extractor_class):
        """Test CLI with password option."""
        # Mock Path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = '.pdf'
        mock_path_instance.__str__ = Mock(return_value='test.pdf')
        mock_path.return_value = mock_path_instance
        
        # Mock BoletoExtractor
        mock_extractor = Mock()
        mock_extractor.extract_boleto_numbers.return_value = ['19790000050457284935662771035649711690000038600']
        mock_extractor_class.return_value = mock_extractor
        
        # Mock print to capture output
        with patch('builtins.print') as mock_print:
            main()
            
            # Verify extractor was called with password
            mock_extractor.extract_boleto_numbers.assert_called_once()
            call_args = mock_extractor.extract_boleto_numbers.call_args
            self.assertEqual(str(call_args[0][0]), 'test.pdf')
            self.assertEqual(call_args[0][1], 'mypassword')

    @patch('boleto_extractor.cli.Path')
    @patch('sys.argv', ['boleto-extractor', 'nonexistent.pdf'])
    @patch('sys.exit')
    def test_cli_file_not_found(self, mock_exit, mock_path):
        """Test CLI with non-existent file."""
        # Mock Path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance
        
        # Mock logger to capture error
        with self.assertLogs(level='ERROR'):
            main()
            
        # Verify sys.exit was called
        mock_exit.assert_called_with(1)

    @patch('boleto_extractor.cli.Path')
    @patch('sys.argv', ['boleto-extractor', 'test.txt'])
    @patch('sys.exit')
    def test_cli_not_pdf_file(self, mock_exit, mock_path):
        """Test CLI with non-PDF file."""
        # Mock Path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = '.txt'
        mock_path.return_value = mock_path_instance
        
        # Mock logger to capture error
        with self.assertLogs(level='ERROR'):
            main()
            
        # Verify sys.exit was called
        mock_exit.assert_called_with(1)

    @patch('boleto_extractor.cli.BoletoExtractor')
    @patch('boleto_extractor.cli.Path')
    @patch('sys.argv', ['boleto-extractor', 'test.pdf'])
    @patch('sys.exit')
    def test_cli_no_boleto_numbers_found(self, mock_exit, mock_path, mock_extractor_class):
        """Test CLI when no boleto numbers are found."""
        # Mock Path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = '.pdf'
        mock_path_instance.__str__ = Mock(return_value='test.pdf')
        mock_path.return_value = mock_path_instance
        
        # Mock BoletoExtractor
        mock_extractor = Mock()
        mock_extractor.extract_boleto_numbers.return_value = []
        mock_extractor_class.return_value = mock_extractor
        
        # Mock print to capture output
        with patch('builtins.print') as mock_print:
            main()
            
            # Verify "No boleto numbers found" was printed
            mock_print.assert_called_with("No boleto numbers found.")

    @patch('boleto_extractor.cli.BoletoExtractor')
    @patch('boleto_extractor.cli.Path')
    @patch('sys.argv', ['boleto-extractor', 'test.pdf'])
    @patch('sys.exit')
    def test_cli_extraction_error(self, mock_exit, mock_path, mock_extractor_class):
        """Test CLI when extraction raises an exception."""
        # Mock Path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = '.pdf'
        mock_path_instance.__str__ = Mock(return_value='test.pdf')
        mock_path.return_value = mock_path_instance
        
        # Mock BoletoExtractor
        mock_extractor = Mock()
        mock_extractor.extract_boleto_numbers.side_effect = Exception("Test error")
        mock_extractor_class.return_value = mock_extractor
        
        # Mock print to capture output
        with patch('builtins.print') as mock_print:
            with self.assertLogs(level='ERROR'):
                main()
            
            # Verify error was logged but no exception was raised
            # (CLI should handle exceptions gracefully)

    @patch('boleto_extractor.cli.BoletoExtractor')
    @patch('boleto_extractor.cli.Path')
    @patch('boleto_extractor.cli.CLIPBOARD_AVAILABLE', False)
    @patch('sys.argv', ['boleto-extractor', 'test.pdf', '--clipboard'])
    @patch('sys.exit')
    def test_cli_clipboard_not_available(self, mock_exit, mock_path, mock_extractor_class):
        """Test CLI with clipboard option when pyperclip is not available."""
        # Mock Path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = '.pdf'
        mock_path_instance.__str__ = Mock(return_value='test.pdf')
        mock_path.return_value = mock_path_instance
        
        # Mock BoletoExtractor
        mock_extractor = Mock()
        mock_extractor.extract_boleto_numbers.return_value = ['19790000050457284935662771035649711690000038600']
        mock_extractor_class.return_value = mock_extractor
        
        # Mock print to capture output
        with patch('builtins.print') as mock_print:
            with self.assertLogs(level='WARNING'):
                main()
            
            # Verify warning was logged about pyperclip not being available

    @patch('boleto_extractor.cli.BoletoExtractor')
    @patch('boleto_extractor.cli.Path')
    @patch('boleto_extractor.cli.CLIPBOARD_AVAILABLE', True)
    @patch('boleto_extractor.cli.pyperclip')
    @patch('sys.argv', ['boleto-extractor', 'test.pdf', '--clipboard'])
    @patch('sys.exit')
    def test_cli_clipboard_error(self, mock_exit, mock_pyperclip, mock_path, mock_extractor_class):
        """Test CLI with clipboard option when pyperclip raises an exception."""
        # Mock Path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = '.pdf'
        mock_path_instance.__str__ = Mock(return_value='test.pdf')
        mock_path.return_value = mock_path_instance
        
        # Mock BoletoExtractor
        mock_extractor = Mock()
        mock_extractor.extract_boleto_numbers.return_value = ['19790000050457284935662771035649711690000038600']
        mock_extractor_class.return_value = mock_extractor
        
        # Mock pyperclip to raise exception
        mock_pyperclip.copy.side_effect = Exception("Clipboard error")
        
        # Mock print to capture output
        with patch('builtins.print') as mock_print:
            with self.assertLogs(level='ERROR'):
                main()
            
            # Verify error was logged about clipboard failure

    @patch('boleto_extractor.cli.BoletoExtractor')
    @patch('boleto_extractor.cli.Path')
    @patch('sys.argv', ['boleto-extractor', 'test.pdf', '--verbose'])
    @patch('sys.exit')
    def test_cli_with_verbose(self, mock_exit, mock_path, mock_extractor_class):
        """Test CLI with verbose option."""
        # Mock Path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = '.pdf'
        mock_path_instance.__str__ = Mock(return_value='test.pdf')
        mock_path.return_value = mock_path_instance
        
        # Mock BoletoExtractor
        mock_extractor = Mock()
        mock_extractor.extract_boleto_numbers.return_value = ['19790000050457284935662771035649711690000038600']
        mock_extractor_class.return_value = mock_extractor
        
        # Mock logging
        with patch('boleto_extractor.cli.logging') as mock_logging:
            with patch('builtins.print') as mock_print:
                main()
                
                # Verify logging level was set to DEBUG
                mock_logging.getLogger.return_value.setLevel.assert_called_with(mock_logging.DEBUG)

    @patch('boleto_extractor.cli.BoletoExtractor')
    @patch('boleto_extractor.cli.Path')
    @patch('sys.argv', ['boleto-extractor', 'test.pdf'])
    @patch('sys.exit')
    def test_cli_multiple_boleto_numbers(self, mock_exit, mock_path, mock_extractor_class):
        """Test CLI with multiple boleto numbers found."""
        # Mock Path
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = '.pdf'
        mock_path_instance.__str__ = Mock(return_value='test.pdf')
        mock_path.return_value = mock_path_instance
        
        # Mock BoletoExtractor
        mock_extractor = Mock()
        mock_extractor.extract_boleto_numbers.return_value = [
            '19790000050457284935662771035649711690000038600',
            '23793381286007700002901000062004675870000002000'
        ]
        mock_extractor_class.return_value = mock_extractor
        
        # Mock print to capture output
        with patch('builtins.print') as mock_print:
            main()
            
            # Verify the count was printed
            calls = mock_print.call_args_list
            found_count_call = any('Found 2 boleto number(s):' in str(call) for call in calls)
            self.assertTrue(found_count_call)


if __name__ == '__main__':
    unittest.main() 