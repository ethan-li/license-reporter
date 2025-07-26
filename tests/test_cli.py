"""
Tests for the CLI module.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from license_reporter.cli import create_parser, main


class TestCreateParser:
    """Tests for create_parser function."""

    def test_create_parser_basic(self):
        """Test basic parser creation."""
        parser = create_parser()
        assert parser.prog is not None
        assert "Universal Python License Report Generator" in parser.description

    def test_parser_default_arguments(self):
        """Test parser with default arguments."""
        parser = create_parser()
        args = parser.parse_args([])
        
        assert args.project_path == "."
        assert args.format == "text"
        assert args.output is None
        assert args.include_dev is False
        assert args.include_optional is False
        assert args.runtime_only is False
        assert args.all_deps is False
        assert args.exclude is None
        assert args.project_name is None
        assert args.legacy_mode is False

    def test_parser_project_path(self):
        """Test parser with project path argument."""
        parser = create_parser()
        args = parser.parse_args(["/path/to/project"])
        
        assert args.project_path == "/path/to/project"

    def test_parser_format_options(self):
        """Test parser with different format options."""
        parser = create_parser()
        
        # Test text format
        args = parser.parse_args(["--format", "text"])
        assert args.format == "text"
        
        # Test JSON format
        args = parser.parse_args(["--format", "json"])
        assert args.format == "json"
        
        # Test Markdown format
        args = parser.parse_args(["--format", "markdown"])
        assert args.format == "markdown"

    def test_parser_output_file(self):
        """Test parser with output file option."""
        parser = create_parser()
        
        # Test long form
        args = parser.parse_args(["--output", "report.txt"])
        assert args.output == "report.txt"
        
        # Test short form
        args = parser.parse_args(["-o", "report.json"])
        assert args.output == "report.json"

    def test_parser_dependency_options(self):
        """Test parser with dependency inclusion options."""
        parser = create_parser()
        
        # Test include dev
        args = parser.parse_args(["--include-dev"])
        assert args.include_dev is True
        
        # Test include optional
        args = parser.parse_args(["--include-optional"])
        assert args.include_optional is True
        
        # Test runtime only
        args = parser.parse_args(["--runtime-only"])
        assert args.runtime_only is True
        
        # Test all deps
        args = parser.parse_args(["--all-deps"])
        assert args.all_deps is True

    def test_parser_filtering_options(self):
        """Test parser with filtering options."""
        parser = create_parser()
        
        # Test exclude patterns
        args = parser.parse_args(["--exclude", "test*,dev*"])
        assert args.exclude == "test*,dev*"
        
        # Test project name override
        args = parser.parse_args(["--project-name", "my-project"])
        assert args.project_name == "my-project"

    def test_parser_legacy_mode(self):
        """Test parser with legacy mode option."""
        parser = create_parser()
        args = parser.parse_args(["--legacy-mode"])
        assert args.legacy_mode is True


class TestMain:
    """Tests for main function."""

    def test_main_nonexistent_path(self, capsys):
        """Test main with nonexistent project path."""
        with patch('sys.argv', ['license-reporter', '/nonexistent/path']):
            result = main()
        
        assert result == 1
        captured = capsys.readouterr()
        assert "does not exist" in captured.out

    @patch('license_reporter.cli.LicenseReporter')
    def test_main_basic_success(self, mock_reporter_class, temp_project_dir, capsys):
        """Test successful basic execution."""
        # Mock the reporter
        mock_reporter = MagicMock()
        mock_reporter_class.return_value = mock_reporter
        mock_reporter.generate_report.return_value = {
            "project": "test-project",
            "packages": [],
            "summary": {
                "total_packages": 0,
                "runtime_packages": 0,
                "dev_packages": 0,
                "optional_packages": 0,
                "requires_attribution": 0
            }
        }
        
        with patch('sys.argv', ['license-reporter', str(temp_project_dir)]):
            result = main()
        
        assert result == 0
        mock_reporter.generate_report.assert_called_once()

    @patch('license_reporter.cli.LicenseReporter')
    def test_main_with_output_file(self, mock_reporter_class, temp_project_dir):
        """Test main with output file."""
        # Mock the reporter
        mock_reporter = MagicMock()
        mock_reporter_class.return_value = mock_reporter
        mock_reporter.generate_report.return_value = {
            "project": "test-project",
            "packages": [],
            "summary": {
                "total_packages": 0,
                "runtime_packages": 0,
                "dev_packages": 0,
                "optional_packages": 0,
                "requires_attribution": 0
            }
        }
        
        output_file = temp_project_dir / "report.txt"
        
        with patch('sys.argv', ['license-reporter', str(temp_project_dir), '-o', str(output_file)]):
            result = main()
        
        assert result == 0
        assert output_file.exists()
        mock_reporter.generate_report.assert_called_once()

    @patch('license_reporter.cli.LicenseReporter')
    def test_main_all_deps_option(self, mock_reporter_class, temp_project_dir):
        """Test main with --all-deps option."""
        mock_reporter = MagicMock()
        mock_reporter_class.return_value = mock_reporter
        mock_reporter.generate_report.return_value = {
            "project": "test-project",
            "packages": [],
            "summary": {"total_packages": 0, "requires_attribution": 0}
        }
        
        with patch('sys.argv', ['license-reporter', str(temp_project_dir), '--all-deps']):
            result = main()
        
        assert result == 0
        # Should call with include_dev=True, include_optional=True, runtime_only=False
        mock_reporter.generate_report.assert_called_once_with(
            include_dev=True,
            include_optional=True,
            runtime_only=False,
            exclude_patterns=[],
            project_name=None
        )

    @patch('license_reporter.cli.LicenseReporter')
    def test_main_runtime_only_option(self, mock_reporter_class, temp_project_dir):
        """Test main with --runtime-only option."""
        mock_reporter = MagicMock()
        mock_reporter_class.return_value = mock_reporter
        mock_reporter.generate_report.return_value = {
            "project": "test-project",
            "packages": [],
            "summary": {"total_packages": 0, "requires_attribution": 0}
        }
        
        with patch('sys.argv', ['license-reporter', str(temp_project_dir), '--runtime-only']):
            result = main()
        
        assert result == 0
        # Should call with runtime_only=True
        mock_reporter.generate_report.assert_called_once_with(
            include_dev=False,
            include_optional=False,
            runtime_only=True,
            exclude_patterns=[],
            project_name=None
        )

    @patch('license_reporter.cli.LicenseReporter')
    def test_main_exclude_patterns(self, mock_reporter_class, temp_project_dir):
        """Test main with exclude patterns."""
        mock_reporter = MagicMock()
        mock_reporter_class.return_value = mock_reporter
        mock_reporter.generate_report.return_value = {
            "project": "test-project",
            "packages": [],
            "summary": {"total_packages": 0, "requires_attribution": 0}
        }
        
        with patch('sys.argv', ['license-reporter', str(temp_project_dir), '--exclude', 'test*,dev*']):
            result = main()
        
        assert result == 0
        # Should call with exclude_patterns
        mock_reporter.generate_report.assert_called_once_with(
            include_dev=False,
            include_optional=False,
            runtime_only=False,
            exclude_patterns=['test*', 'dev*'],
            project_name=None
        )

    @patch('license_reporter.cli.LicenseReporter')
    def test_main_legacy_mode(self, mock_reporter_class, temp_project_dir):
        """Test main with legacy mode."""
        mock_reporter = MagicMock()
        mock_reporter_class.return_value = mock_reporter
        mock_reporter.generate_report.return_value = {
            "project": "OSI (Open Source Installer)",
            "packages": [],
            "summary": {"total_packages": 0, "requires_attribution": 0}
        }
        
        with patch('sys.argv', ['license-reporter', str(temp_project_dir), '--legacy-mode']):
            result = main()
        
        assert result == 0
        # Should call with legacy OSI settings
        mock_reporter.generate_report.assert_called_once_with(
            runtime_only=True,
            project_name="OSI (Open Source Installer)"
        )

    @patch('license_reporter.cli.LicenseReporter')
    def test_main_json_format(self, mock_reporter_class, temp_project_dir, capsys):
        """Test main with JSON format."""
        mock_reporter = MagicMock()
        mock_reporter_class.return_value = mock_reporter
        mock_reporter.generate_report.return_value = {
            "project": "test-project",
            "packages": [],
            "summary": {"total_packages": 0, "requires_attribution": 0}
        }
        
        with patch('sys.argv', ['license-reporter', str(temp_project_dir), '--format', 'json']):
            result = main()
        
        assert result == 0
        captured = capsys.readouterr()
        # Should output valid JSON
        assert '"project": "test-project"' in captured.out

    @patch('license_reporter.cli.LicenseReporter')
    def test_main_error_handling(self, mock_reporter_class, temp_project_dir, capsys):
        """Test main error handling."""
        mock_reporter = MagicMock()
        mock_reporter_class.return_value = mock_reporter
        mock_reporter.generate_report.side_effect = Exception("Test error")
        
        with patch('sys.argv', ['license-reporter', str(temp_project_dir)]):
            result = main()
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Error generating license report" in captured.out
