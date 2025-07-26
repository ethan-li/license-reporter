"""
Tests for the core module.
"""

import pytest
from pathlib import Path

from license_reporter.core import DependencyInfo, LicenseReporter


class TestDependencyInfo:
    """Tests for DependencyInfo class."""

    def test_init_basic(self):
        """Test basic initialization."""
        dep = DependencyInfo("requests")
        assert dep.name == "requests"
        assert dep.version_spec == ""
        assert dep.dep_type == "runtime"

    def test_init_with_version_spec(self):
        """Test initialization with version specification."""
        dep = DependencyInfo("requests", ">=2.25.0", "dev")
        assert dep.name == "requests"
        assert dep.version_spec == ">=2.25.0"
        assert dep.dep_type == "dev"

    def test_init_strips_whitespace(self):
        """Test that whitespace is stripped from name and version_spec."""
        dep = DependencyInfo("  requests  ", "  >=2.25.0  ")
        assert dep.name == "requests"
        assert dep.version_spec == ">=2.25.0"

    def test_repr(self):
        """Test string representation."""
        dep = DependencyInfo("requests", ">=2.25.0", "dev")
        expected = "DependencyInfo(requests, >=2.25.0, dev)"
        assert repr(dep) == expected

    def test_equality(self):
        """Test equality comparison."""
        dep1 = DependencyInfo("requests", ">=2.25.0", "dev")
        dep2 = DependencyInfo("requests", ">=2.25.0", "dev")
        dep3 = DependencyInfo("click", ">=8.0.0", "runtime")

        assert dep1 == dep2
        assert dep1 != dep3
        assert dep1 != "not a dependency"

    def test_hash(self):
        """Test that DependencyInfo objects are hashable."""
        dep1 = DependencyInfo("requests", ">=2.25.0", "dev")
        dep2 = DependencyInfo("requests", ">=2.25.0", "dev")

        # Should be able to create a set
        deps_set = {dep1, dep2}
        assert len(deps_set) == 1  # Should be deduplicated


class TestLicenseReporter:
    """Tests for LicenseReporter class."""

    def test_init_default_path(self):
        """Test initialization with default path."""
        reporter = LicenseReporter()
        assert reporter.project_root == Path.cwd()

    def test_init_custom_path(self, temp_project_dir):
        """Test initialization with custom path."""
        reporter = LicenseReporter(temp_project_dir)
        assert reporter.project_root == temp_project_dir

    def test_requires_attribution_mit(self):
        """Test attribution requirement for MIT license."""
        reporter = LicenseReporter()
        assert reporter._requires_attribution("MIT License") is True
        assert reporter._requires_attribution("mit") is True

    def test_requires_attribution_bsd(self):
        """Test attribution requirement for BSD license."""
        reporter = LicenseReporter()
        assert reporter._requires_attribution("BSD License") is True
        assert reporter._requires_attribution("bsd-3-clause") is True

    def test_requires_attribution_apache(self):
        """Test attribution requirement for Apache license."""
        reporter = LicenseReporter()
        assert reporter._requires_attribution("Apache Software License") is True
        assert reporter._requires_attribution("apache 2.0") is True

    def test_requires_attribution_public_domain(self):
        """Test no attribution requirement for public domain."""
        reporter = LicenseReporter()
        assert reporter._requires_attribution("Public Domain") is False
        assert reporter._requires_attribution("public domain") is False

    def test_requires_attribution_unlicense(self):
        """Test no attribution requirement for Unlicense."""
        reporter = LicenseReporter()
        assert reporter._requires_attribution("Unlicense") is False
        assert reporter._requires_attribution("unlicense") is False

    def test_requires_attribution_unknown(self):
        """Test conservative default for unknown licenses."""
        reporter = LicenseReporter()
        assert reporter._requires_attribution("Unknown License") is True
        assert reporter._requires_attribution("") is True

    def test_matches_pattern_exact(self):
        """Test exact pattern matching."""
        reporter = LicenseReporter()
        assert reporter._matches_pattern("requests", "requests") is True
        assert reporter._matches_pattern("requests", "click") is False

    def test_matches_pattern_wildcard(self):
        """Test wildcard pattern matching."""
        reporter = LicenseReporter()
        assert reporter._matches_pattern("pytest-cov", "pytest*") is True
        assert reporter._matches_pattern("pytest-mock", "pytest*") is True
        assert reporter._matches_pattern("requests", "pytest*") is False

    def test_matches_pattern_question_mark(self):
        """Test single character wildcard pattern matching."""
        reporter = LicenseReporter()
        assert reporter._matches_pattern("test1", "test?") is True
        assert reporter._matches_pattern("test2", "test?") is True
        assert reporter._matches_pattern("test12", "test?") is False

    def test_filter_dependencies_runtime_only(self):
        """Test filtering for runtime dependencies only."""
        reporter = LicenseReporter()
        deps = [
            DependencyInfo("requests", ">=2.25.0", "runtime"),
            DependencyInfo("pytest", ">=7.0.0", "dev"),
            DependencyInfo("sphinx", ">=5.0.0", "optional"),
        ]

        filtered = reporter.filter_dependencies(deps, runtime_only=True)
        assert len(filtered) == 1
        assert filtered[0].name == "requests"

    def test_filter_dependencies_include_dev(self):
        """Test filtering with development dependencies included."""
        reporter = LicenseReporter()
        deps = [
            DependencyInfo("requests", ">=2.25.0", "runtime"),
            DependencyInfo("pytest", ">=7.0.0", "dev"),
            DependencyInfo("sphinx", ">=5.0.0", "optional"),
        ]

        filtered = reporter.filter_dependencies(deps, include_dev=True)
        assert len(filtered) == 2
        names = {dep.name for dep in filtered}
        assert names == {"requests", "pytest"}

    def test_filter_dependencies_exclude_patterns(self):
        """Test filtering with exclude patterns."""
        reporter = LicenseReporter()
        deps = [
            DependencyInfo("requests", ">=2.25.0", "runtime"),
            DependencyInfo("pytest", ">=7.0.0", "runtime"),
            DependencyInfo("pytest-cov", ">=4.0.0", "runtime"),
        ]

        filtered = reporter.filter_dependencies(deps, exclude_patterns=["pytest*"])
        assert len(filtered) == 1
        assert filtered[0].name == "requests"

    def test_filter_dependencies_build_time_packages(self):
        """Test filtering out build-time packages in runtime-only mode."""
        reporter = LicenseReporter()
        deps = [
            DependencyInfo("requests", ">=2.25.0", "runtime"),
            DependencyInfo("setuptools", ">=60.0.0", "runtime"),  # Build-time package
            DependencyInfo("pytest", ">=7.0.0", "runtime"),  # Test package
        ]

        filtered = reporter.filter_dependencies(deps, runtime_only=True)
        assert len(filtered) == 1
        assert filtered[0].name == "requests"

    def test_detect_project_name_fallback(self, temp_project_dir):
        """Test project name detection fallback to directory name."""
        reporter = LicenseReporter(temp_project_dir)
        project_name = reporter._detect_project_name()
        assert project_name == temp_project_dir.name

    def test_get_package_info_unknown_package(self):
        """Test getting package info for unknown package."""
        reporter = LicenseReporter()
        info = reporter.get_package_info("nonexistent-package-12345")

        assert info["name"] == "nonexistent-package-12345"
        assert info["version"] == "unknown"
        assert info["license"] == "unknown"
        assert info["author"] == "unknown"
        assert info["homepage"] == "unknown"
        assert info["requires_attribution"] is True
