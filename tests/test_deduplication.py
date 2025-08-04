"""
Tests for dependency deduplication functionality.

This module tests that dependencies appearing in multiple files are properly
deduplicated in the final report.
"""

import tempfile
from pathlib import Path

import pytest

from license_reporter.core import LicenseReporter
from license_reporter.parsers import DependencyParser


class TestDeduplication:
    """Test dependency deduplication across multiple files."""

    def test_duplicate_dependencies_across_files(self, tmp_path):
        """Test that dependencies appearing in multiple files are deduplicated."""
        # Create a project with both requirements.txt and pyproject.toml
        # containing the same dependency

        # Create requirements.txt
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("requests>=2.25.0\nclick>=8.0.0\n")

        # Create pyproject.toml with overlapping dependencies
        pyproject_toml = tmp_path / "pyproject.toml"
        pyproject_toml.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"
dependencies = [
    "requests>=2.25.0",
    "numpy>=1.20.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "click>=8.0.0"
]
"""
        )

        # Parse dependencies
        parser = DependencyParser(tmp_path)
        all_deps = parser.get_all_dependencies()

        # Check that we have duplicates before deduplication
        dep_names = [dep.name for dep in all_deps]
        assert (
            dep_names.count("requests") > 1
        ), "Should have duplicate 'requests' entries"
        assert dep_names.count("click") > 1, "Should have duplicate 'click' entries"

        # Generate report
        reporter = LicenseReporter(tmp_path)
        report = reporter.generate_report(include_dev=True)

        # Check that duplicates are removed in final report
        package_names = [pkg["name"] for pkg in report["packages"]]
        assert (
            package_names.count("requests") == 1
        ), "Should have only one 'requests' entry in report"
        assert (
            package_names.count("click") == 1
        ), "Should have only one 'click' entry in report"
        assert (
            package_names.count("numpy") == 1
        ), "Should have only one 'numpy' entry in report"
        assert (
            package_names.count("pytest") == 1
        ), "Should have only one 'pytest' entry in report"

    def test_version_spec_priority(self, tmp_path):
        """Test that more specific version specs are preserved during deduplication."""
        # Create requirements.txt with loose version
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("requests>=2.0.0\n")

        # Create pyproject.toml with more specific version
        pyproject_toml = tmp_path / "pyproject.toml"
        pyproject_toml.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"
dependencies = [
    "requests>=2.25.0"
]
"""
        )

        # Generate report
        reporter = LicenseReporter(tmp_path)
        report = reporter.generate_report()

        # Find the requests package in the report
        requests_pkg = next(
            pkg for pkg in report["packages"] if pkg["name"] == "requests"
        )

        # Should preserve the more specific version spec
        assert (
            requests_pkg["version_spec"] == ">=2.25.0"
        ), "Should preserve more specific version"

    def test_dependency_type_preservation(self, tmp_path):
        """Test that dependency types are properly handled during deduplication."""
        # Create requirements.txt with runtime dependency
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("pytest>=7.0.0\n")

        # Create pyproject.toml with same package as dev dependency
        pyproject_toml = tmp_path / "pyproject.toml"
        pyproject_toml.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0"
]
"""
        )

        # Generate report including dev dependencies
        reporter = LicenseReporter(tmp_path)
        report = reporter.generate_report(include_dev=True)

        # Should have only one pytest entry
        pytest_packages = [pkg for pkg in report["packages"] if pkg["name"] == "pytest"]
        assert len(pytest_packages) == 1, "Should have only one pytest entry"

        # Should preserve the most appropriate dependency type
        pytest_pkg = pytest_packages[0]
        assert pytest_pkg["dependency_type"] in [
            "runtime",
            "dev",
        ], "Should have valid dependency type"

    def test_source_information_tracking(self, tmp_path):
        """Test that source file information is tracked for transparency."""
        # Create multiple files with the same dependency
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("requests>=2.25.0\n")

        pyproject_toml = tmp_path / "pyproject.toml"
        pyproject_toml.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"
dependencies = [
    "requests>=2.25.0"
]
"""
        )

        # Generate report
        reporter = LicenseReporter(tmp_path)
        report = reporter.generate_report()

        # Check that dependency files are listed
        assert (
            len(report["dependency_files"]) >= 2
        ), "Should list multiple dependency files"
        assert any(
            "requirements.txt" in f for f in report["dependency_files"]
        ), "Should include requirements.txt"
        assert any(
            "pyproject.toml" in f for f in report["dependency_files"]
        ), "Should include pyproject.toml"

    def test_exact_version_priority(self, tmp_path):
        """Test that exact versions (==) take priority over ranges."""
        # Create requirements.txt with range version
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("requests>=2.0.0\n")

        # Create setup.py with exact version
        setup_py = tmp_path / "setup.py"
        setup_py.write_text(
            """
from setuptools import setup
setup(
    name="test-project",
    install_requires=["requests==2.28.1"]
)
"""
        )

        # Generate report
        reporter = LicenseReporter(tmp_path)
        report = reporter.generate_report()

        # Find the requests package in the report
        requests_pkg = next(
            pkg for pkg in report["packages"] if pkg["name"] == "requests"
        )

        # Should preserve the exact version
        assert (
            requests_pkg["version_spec"] == "==2.28.1"
        ), "Should preserve exact version over range"

    def test_case_insensitive_deduplication(self, tmp_path):
        """Test that package names are deduplicated case-insensitively."""
        # Create requirements.txt with lowercase
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("requests>=2.25.0\n")

        # Create pyproject.toml with different case
        pyproject_toml = tmp_path / "pyproject.toml"
        pyproject_toml.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"
dependencies = [
    "Requests>=2.30.0"
]
"""
        )

        # Generate report
        reporter = LicenseReporter(tmp_path)
        report = reporter.generate_report()

        # Should have only one requests entry
        requests_packages = [
            pkg for pkg in report["packages"] if pkg["name"].lower() == "requests"
        ]
        assert (
            len(requests_packages) == 1
        ), "Should deduplicate case-insensitive package names"

    def test_empty_version_specs(self, tmp_path):
        """Test handling of empty or missing version specifications."""
        # Create requirements.txt with no version
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("requests\n")

        # Create pyproject.toml with version
        pyproject_toml = tmp_path / "pyproject.toml"
        pyproject_toml.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"
dependencies = [
    "requests>=2.25.0"
]
"""
        )

        # Generate report
        reporter = LicenseReporter(tmp_path)
        report = reporter.generate_report()

        # Should preserve the version spec from pyproject.toml
        requests_pkg = next(
            pkg for pkg in report["packages"] if pkg["name"] == "requests"
        )
        assert (
            requests_pkg["version_spec"] == ">=2.25.0"
        ), "Should preserve non-empty version spec"

    def test_complex_version_comparison(self, tmp_path):
        """Test complex version specification comparison."""
        # Create multiple files with different version specs
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("numpy>=1.20.0\n")

        requirements_dev_txt = tmp_path / "requirements-dev.txt"
        requirements_dev_txt.write_text("numpy>=1.22.0\n")

        pyproject_toml = tmp_path / "pyproject.toml"
        pyproject_toml.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"
dependencies = [
    "numpy>=1.21.0"
]
"""
        )

        # Generate report
        reporter = LicenseReporter(tmp_path)
        report = reporter.generate_report()

        # Should preserve the highest minimum version
        numpy_pkg = next(pkg for pkg in report["packages"] if pkg["name"] == "numpy")
        assert (
            numpy_pkg["version_spec"] == ">=1.22.0"
        ), "Should preserve highest minimum version"
