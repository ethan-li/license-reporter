"""
Integration tests for the license reporter.

These tests verify that all components work together correctly.
"""

import json
from pathlib import Path
import pytest

from license_reporter.core import LicenseReporter
from license_reporter.parsers import DependencyParser
from license_reporter.formatters import get_formatter


class TestIntegration:
    """Integration tests for the complete license reporting workflow."""

    def test_end_to_end_requirements_txt(self, temp_project_dir, sample_requirements_txt):
        """Test complete workflow with requirements.txt."""
        reporter = LicenseReporter(temp_project_dir)
        
        # Generate report
        report = reporter.generate_report()
        
        # Verify report structure
        assert "project" in report
        assert "packages" in report
        assert "summary" in report
        assert "dependency_files" in report
        
        # Verify packages were found
        assert len(report["packages"]) > 0
        package_names = {pkg["name"] for pkg in report["packages"]}
        assert "requests" in package_names
        assert "click" in package_names
        
        # Verify summary
        assert report["summary"]["total_packages"] == len(report["packages"])
        assert report["summary"]["runtime_packages"] > 0

    def test_end_to_end_multiple_files(self, temp_project_dir, sample_requirements_txt, 
                                     sample_dev_requirements_txt):
        """Test complete workflow with multiple dependency files."""
        reporter = LicenseReporter(temp_project_dir)
        
        # Generate report including dev dependencies
        report = reporter.generate_report(include_dev=True)
        
        # Should find dependencies from both files
        package_names = {pkg["name"] for pkg in report["packages"]}
        
        # From requirements.txt
        assert "requests" in package_names
        assert "click" in package_names
        
        # From dev-requirements.txt
        assert "pytest" in package_names
        assert "black" in package_names
        
        # Verify dependency types
        runtime_packages = [pkg for pkg in report["packages"] if pkg["dependency_type"] == "runtime"]
        dev_packages = [pkg for pkg in report["packages"] if pkg["dependency_type"] == "dev"]
        
        assert len(runtime_packages) > 0
        assert len(dev_packages) > 0
        
        # Verify summary counts
        assert report["summary"]["runtime_packages"] == len(runtime_packages)
        assert report["summary"]["dev_packages"] == len(dev_packages)

    def test_end_to_end_pyproject_toml(self, temp_project_dir, sample_pyproject_toml):
        """Test complete workflow with pyproject.toml."""
        reporter = LicenseReporter(temp_project_dir)
        
        # Generate report including all dependencies
        report = reporter.generate_report(include_dev=True, include_optional=True)
        
        # Should detect project name from pyproject.toml
        assert report["project"] == "test-project"
        
        # Should find dependencies
        package_names = {pkg["name"] for pkg in report["packages"]}
        assert len(package_names) > 0

    def test_runtime_only_filtering(self, temp_project_dir, sample_requirements_txt, 
                                  sample_dev_requirements_txt):
        """Test runtime-only filtering excludes dev dependencies."""
        reporter = LicenseReporter(temp_project_dir)
        
        # Generate runtime-only report
        report = reporter.generate_report(runtime_only=True)
        
        # Should only include runtime dependencies
        for package in report["packages"]:
            assert package["dependency_type"] == "runtime"
        
        # Should exclude dev packages
        package_names = {pkg["name"] for pkg in report["packages"]}
        assert "pytest" not in package_names  # Dev dependency
        assert "black" not in package_names   # Dev dependency

    def test_exclude_patterns(self, temp_project_dir, sample_requirements_txt):
        """Test exclude patterns functionality."""
        reporter = LicenseReporter(temp_project_dir)
        
        # Generate report excluding packages starting with 'r'
        report = reporter.generate_report(exclude_patterns=["r*"])
        
        # Should exclude 'requests' but include others
        package_names = {pkg["name"] for pkg in report["packages"]}
        assert "requests" not in package_names
        assert "click" in package_names

    def test_all_output_formats(self, temp_project_dir, sample_requirements_txt):
        """Test that all output formats work correctly."""
        reporter = LicenseReporter(temp_project_dir)
        report = reporter.generate_report()
        
        # Test text format
        text_formatter = get_formatter("text")
        text_output = text_formatter.format(report)
        assert "THIRD-PARTY SOFTWARE LICENSES" in text_output
        assert "requests" in text_output
        
        # Test JSON format
        json_formatter = get_formatter("json")
        json_output = json_formatter.format(report)
        parsed_json = json.loads(json_output)
        assert parsed_json["project"] == report["project"]
        
        # Test Markdown format
        markdown_formatter = get_formatter("markdown")
        markdown_output = markdown_formatter.format(report)
        assert "# Third-Party Software Licenses" in markdown_output
        assert "| requests |" in markdown_output

    def test_project_name_detection(self, temp_project_dir, sample_pyproject_toml):
        """Test project name detection from various sources."""
        reporter = LicenseReporter(temp_project_dir)
        
        # Should detect name from pyproject.toml
        project_name = reporter._detect_project_name()
        assert project_name == "test-project"
        
        # Test fallback to directory name
        reporter_no_files = LicenseReporter(temp_project_dir)
        # Remove pyproject.toml
        sample_pyproject_toml.unlink()
        fallback_name = reporter_no_files._detect_project_name()
        assert fallback_name == temp_project_dir.name

    def test_dependency_file_discovery(self, temp_project_dir, sample_requirements_txt, 
                                     sample_pyproject_toml, sample_setup_py):
        """Test that all dependency files are discovered."""
        parser = DependencyParser(temp_project_dir)
        files = parser.discover_dependency_files()
        
        expected_files = {"requirements.txt", "pyproject.toml", "setup.py"}
        assert set(files.keys()) == expected_files
        
        # Verify paths are correct
        assert files["requirements.txt"] == sample_requirements_txt
        assert files["pyproject.toml"] == sample_pyproject_toml
        assert files["setup.py"] == sample_setup_py

    def test_license_attribution_detection(self, temp_project_dir):
        """Test license attribution requirement detection."""
        reporter = LicenseReporter(temp_project_dir)
        
        # Test various license types
        assert reporter._requires_attribution("MIT License") is True
        assert reporter._requires_attribution("BSD License") is True
        assert reporter._requires_attribution("Apache Software License") is True
        assert reporter._requires_attribution("Public Domain") is False
        assert reporter._requires_attribution("Unlicense") is False
        assert reporter._requires_attribution("Unknown") is True  # Conservative default

    def test_empty_project(self, temp_project_dir):
        """Test handling of project with no dependencies."""
        reporter = LicenseReporter(temp_project_dir)
        report = reporter.generate_report()
        
        # Should generate valid report with no packages
        assert report["packages"] == []
        assert report["summary"]["total_packages"] == 0
        assert report["summary"]["runtime_packages"] == 0
        assert report["summary"]["dev_packages"] == 0
        
        # Should still be formattable
        text_formatter = get_formatter("text")
        text_output = text_formatter.format(report)
        assert "Total packages: 0" in text_output

    def test_build_time_package_exclusion(self, temp_project_dir):
        """Test that build-time packages are excluded in runtime-only mode."""
        # Create requirements.txt with build-time packages
        requirements_content = """
requests>=2.25.0
setuptools>=60.0.0
pytest>=7.0.0
wheel>=0.37.0
"""
        requirements_file = temp_project_dir / "requirements.txt"
        requirements_file.write_text(requirements_content)
        
        reporter = LicenseReporter(temp_project_dir)
        
        # Runtime-only should exclude build tools
        runtime_report = reporter.generate_report(runtime_only=True)
        runtime_names = {pkg["name"] for pkg in runtime_report["packages"]}
        
        assert "requests" in runtime_names  # Should be included
        assert "setuptools" not in runtime_names  # Should be excluded
        assert "pytest" not in runtime_names  # Should be excluded
        assert "wheel" not in runtime_names  # Should be excluded

    @pytest.mark.slow
    def test_performance_large_project(self, temp_project_dir):
        """Test performance with a larger number of dependencies."""
        # Create a requirements file with many dependencies
        many_deps = [f"package-{i}>=1.0.0" for i in range(100)]
        requirements_content = "\n".join(many_deps)
        requirements_file = temp_project_dir / "requirements.txt"
        requirements_file.write_text(requirements_content)
        
        reporter = LicenseReporter(temp_project_dir)
        
        # Should complete in reasonable time
        import time
        start_time = time.time()
        report = reporter.generate_report()
        end_time = time.time()
        
        # Should find all dependencies (even if package info is unknown)
        assert len(report["packages"]) == 100
        
        # Should complete in under 10 seconds (generous limit)
        assert (end_time - start_time) < 10.0
