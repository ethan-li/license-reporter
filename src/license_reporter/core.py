"""
Core classes and functionality for license reporting.

This module contains the main LicenseReporter class and DependencyInfo data structure.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

try:
    import pkg_resources
except ImportError:
    pkg_resources = None


class DependencyInfo:
    """
    Information about a Python package dependency.

    This class represents a single dependency with its name, version specification,
    and type (runtime, development, optional, or build-time).

    Attributes:
        name (str): The package name (e.g., 'requests')
        version_spec (str): Version specification (e.g., '>=2.25.0', '==1.0.0')
        dep_type (str): Dependency type - 'runtime', 'dev', 'optional', or 'build'

    Example:
        >>> dep = DependencyInfo('requests', '>=2.25.0', 'runtime')
        >>> print(dep.name)
        'requests'
        >>> print(dep.version_spec)
        '>=2.25.0'
        >>> print(dep.dep_type)
        'runtime'
    """

    def __init__(self, name: str, version_spec: str = "", dep_type: str = "runtime"):
        """Initialize dependency information.

        Args:
            name: Package name
            version_spec: Version specification (e.g., ">=1.0.0")
            dep_type: Type of dependency (runtime, dev, optional, build)
        """
        self.name = name.strip()
        self.version_spec = version_spec.strip()
        self.dep_type = dep_type  # runtime, dev, optional, build

    def __repr__(self):
        return f"DependencyInfo({self.name}, {self.version_spec}, {self.dep_type})"

    def __eq__(self, other):
        if not isinstance(other, DependencyInfo):
            return False
        return (
            self.name == other.name
            and self.version_spec == other.version_spec
            and self.dep_type == other.dep_type
        )

    def __hash__(self):
        return hash((self.name, self.version_spec, self.dep_type))


class LicenseReporter:
    """
    Universal license report generator for Python projects.

    This class analyzes Python projects to identify dependencies and generate
    comprehensive license compliance reports. It supports multiple dependency
    file formats and provides various filtering and output options.

    The reporter can analyze:
    - requirements.txt files (and variants)
    - setup.py and setup.cfg files
    - pyproject.toml files (PEP 621 and Poetry formats)
    - Pipfile (Pipenv)
    - environment.yml (Conda)

    Features:
    - Automatic dependency classification (runtime, dev, optional)
    - License detection and attribution analysis
    - Build-time package filtering for PyInstaller compliance
    - Pattern-based package exclusion
    - Multiple output formats (text, JSON, Markdown)

    Example:
        >>> reporter = LicenseReporter('/path/to/project')
        >>> report = reporter.generate_report(runtime_only=True)
        >>> print(f"Found {report['summary']['total_packages']} packages")
    """

    def __init__(self, project_path: Path = None):
        """Initialize the license reporter.

        Args:
            project_path: Path to the project directory to analyze.
                         If None, uses current directory.
        """
        self.project_root = Path(project_path) if project_path else Path.cwd()

        # Build-time dependencies that should be excluded from runtime reports
        self.build_time_packages = {
            "pip",
            "setuptools",
            "wheel",
            "build",
            "twine",
            "virtualenv",
            "venv",
            "pyinstaller",
            "pytest",
            "mypy",
            "black",
            "flake8",
            "isort",
            "coverage",
            "tox",
            "pre-commit",
            "sphinx",
            "mkdocs",
            "jupyter",
            "notebook",
            "ipython",
            "ipykernel",
            "conda",
            "mamba",
            "poetry",
            "pipenv",
            "flit",
            "hatch",
            "pdm",
            "bandit",
            "safety",
            "autopep8",
            "yapf",
            "pylint",
            "pydocstyle",
            "pycodestyle",
            "pyflakes",
            "mccabe",
        }

        # Type stub packages (not bundled in PyInstaller)
        self.type_stub_packages = {
            "types-",
            "typing-extensions",
            "mypy-extensions",
            "stub-",
        }

        # Testing frameworks and related packages
        self.test_packages = {
            "pytest",
            "unittest2",
            "nose",
            "nose2",
            "testtools",
            "mock",
            "pytest-cov",
            "pytest-xdist",
            "pytest-mock",
            "factory-boy",
            "faker",
            "hypothesis",
            "tox",
            "coverage",
            "codecov",
        }

    def get_package_info(self, package_name: str) -> Dict:
        """Get package information including license.

        Args:
            package_name: Name of the package to analyze

        Returns:
            Dictionary containing package information
        """
        info = {
            "name": package_name,
            "version": "unknown",
            "license": "unknown",
            "author": "unknown",
            "homepage": "unknown",
            "requires_attribution": True,  # Conservative default
        }

        try:
            if pkg_resources:
                dist = pkg_resources.get_distribution(package_name)
                info["version"] = dist.version

                # Try to get license from metadata
                if hasattr(dist, "get_metadata"):
                    try:
                        metadata = dist.get_metadata("METADATA")
                        for line in metadata.split("\n"):
                            if line.startswith("License:"):
                                info["license"] = line.split(":", 1)[1].strip()
                            elif line.startswith("Author:"):
                                info["author"] = line.split(":", 1)[1].strip()
                            elif line.startswith("Home-page:"):
                                info["homepage"] = line.split(":", 1)[1].strip()
                    except:
                        pass

        except Exception:
            pass

        # Determine if attribution is required
        info["requires_attribution"] = self._requires_attribution(info["license"])

        return info

    def _requires_attribution(self, license_text: str) -> bool:
        """Determine if a license requires attribution.

        Args:
            license_text: License text to analyze

        Returns:
            True if attribution is required, False otherwise
        """
        license_lower = license_text.lower()

        # Licenses that require attribution
        attribution_required = [
            "mit",
            "bsd",
            "apache",
            "isc",
            "mpl",
            "mozilla",
            "creative commons",
            "cc-by",
        ]

        # Licenses that don't require attribution
        no_attribution = ["public domain", "unlicense", "wtfpl"]

        for license_type in no_attribution:
            if license_type in license_lower:
                return False

        for license_type in attribution_required:
            if license_type in license_lower:
                return True

        # Conservative default: require attribution if unknown
        return True

    def filter_dependencies(
        self,
        dependencies: List[DependencyInfo],
        include_dev: bool = False,
        include_optional: bool = False,
        runtime_only: bool = False,
        exclude_patterns: List[str] = None,
    ) -> List[DependencyInfo]:
        """Filter dependencies based on criteria.

        Args:
            dependencies: List of dependencies to filter
            include_dev: Include development dependencies
            include_optional: Include optional dependencies
            runtime_only: Only include runtime dependencies
            exclude_patterns: List of patterns to exclude (supports wildcards)

        Returns:
            Filtered list of dependencies
        """
        filtered = []
        exclude_patterns = exclude_patterns or []

        for dep in dependencies:
            # Skip if package name matches exclude patterns
            if any(
                self._matches_pattern(dep.name, pattern) for pattern in exclude_patterns
            ):
                continue

            # Filter by dependency type
            if runtime_only and dep.dep_type != "runtime":
                continue

            if not include_dev and dep.dep_type == "dev":
                continue

            if not include_optional and dep.dep_type == "optional":
                continue

            # Exclude build-time packages for runtime-only reports
            if runtime_only and dep.name.lower() in self.build_time_packages:
                continue

            # Exclude type stub packages for runtime-only reports
            if runtime_only and any(
                dep.name.startswith(stub) for stub in self.type_stub_packages
            ):
                continue

            # Exclude test packages for runtime-only reports
            if runtime_only and dep.name.lower() in self.test_packages:
                continue

            filtered.append(dep)

        return filtered

    def _matches_pattern(self, name: str, pattern: str) -> bool:
        """Check if package name matches a pattern (supports wildcards).

        Args:
            name: Package name to check
            pattern: Pattern to match against (supports * and ?)

        Returns:
            True if name matches pattern, False otherwise
        """
        import re

        # Convert shell-style wildcards to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        return bool(re.match(f"^{regex_pattern}$", name, re.IGNORECASE))

    def get_runtime_dependencies(self) -> Set[str]:
        """Get list of packages that are actually bundled in PyInstaller executable.

        This method is kept for backward compatibility with OSI integration.

        Returns:
            Set of runtime dependency names
        """
        from .parsers import DependencyParser

        parser = DependencyParser(self.project_root)
        all_deps = parser.get_all_dependencies()
        runtime_deps = self.filter_dependencies(all_deps, runtime_only=True)
        return {dep.name for dep in runtime_deps}

    def get_requirements_packages(self) -> List[str]:
        """Get list of packages from requirements.txt (legacy method).

        Returns:
            List of package names
        """
        return list(self.get_runtime_dependencies())

    def _detect_project_name(self) -> str:
        """Attempt to detect the project name from various sources.

        Returns:
            Detected or fallback project name
        """
        try:
            import toml
        except ImportError:
            toml = None

        # Try pyproject.toml first
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists() and toml:
            try:
                with open(pyproject_path, "r", encoding="utf-8") as f:
                    data = toml.load(f)
                if "project" in data and "name" in data["project"]:
                    return data["project"]["name"]
                if (
                    "tool" in data
                    and "poetry" in data["tool"]
                    and "name" in data["tool"]["poetry"]
                ):
                    return data["tool"]["poetry"]["name"]
            except:
                pass

        # Try setup.py
        setup_path = self.project_root / "setup.py"
        if setup_path.exists():
            try:
                with open(setup_path, "r", encoding="utf-8") as f:
                    content = f.read()
                import re

                match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
            except:
                pass

        # Fall back to directory name
        return self.project_root.name

    def generate_report(
        self,
        include_dev: bool = False,
        include_optional: bool = False,
        runtime_only: bool = False,
        exclude_patterns: List[str] = None,
        project_name: str = None,
    ) -> Dict:
        """Generate comprehensive license report.

        Args:
            include_dev: Include development dependencies
            include_optional: Include optional dependencies
            runtime_only: Only include runtime dependencies (for PyInstaller compliance)
            exclude_patterns: List of patterns to exclude (supports wildcards)
            project_name: Name of the project being analyzed

        Returns:
            Dictionary containing the complete report
        """
        from .parsers import DependencyParser

        # Get all dependencies and filter them
        parser = DependencyParser(self.project_root)
        all_deps = parser.get_all_dependencies()
        filtered_deps = self.filter_dependencies(
            all_deps,
            include_dev=include_dev,
            include_optional=include_optional,
            runtime_only=runtime_only,
            exclude_patterns=exclude_patterns,
        )

        # Determine report type
        if runtime_only:
            report_type = "Runtime Dependencies (PyInstaller Bundled)"
        elif include_dev and include_optional:
            report_type = "All Dependencies (Runtime + Development + Optional)"
        elif include_dev:
            report_type = "Runtime + Development Dependencies"
        else:
            report_type = "Runtime Dependencies"

        # Detect project name if not provided
        if not project_name:
            project_name = self._detect_project_name()

        report = {
            "project": project_name,
            "project_path": str(self.project_root),
            "generated_by": "Universal Python License Reporter",
            "report_type": report_type,
            "dependency_files": [
                str(f) for f in parser.discover_dependency_files().values()
            ],
            "packages": [],
            "summary": {
                "total_packages": 0,
                "runtime_packages": 0,
                "dev_packages": 0,
                "optional_packages": 0,
                "requires_attribution": 0,
                "unknown_licenses": 0,
            },
            "excluded_build_tools": (
                list(self.build_time_packages) if runtime_only else []
            ),
            "filters_applied": {
                "include_dev": include_dev,
                "include_optional": include_optional,
                "runtime_only": runtime_only,
                "exclude_patterns": exclude_patterns or [],
            },
        }

        # Process each dependency
        for dep in sorted(filtered_deps, key=lambda x: x.name.lower()):
            package_info = self.get_package_info(dep.name)
            package_info["dependency_type"] = dep.dep_type
            package_info["version_spec"] = dep.version_spec
            report["packages"].append(package_info)

            # Update summary counts
            if dep.dep_type == "runtime":
                report["summary"]["runtime_packages"] += 1
            elif dep.dep_type == "dev":
                report["summary"]["dev_packages"] += 1
            elif dep.dep_type == "optional":
                report["summary"]["optional_packages"] += 1

            if package_info["requires_attribution"]:
                report["summary"]["requires_attribution"] += 1
            if package_info["license"] == "unknown":
                report["summary"]["unknown_licenses"] += 1

        report["summary"]["total_packages"] = len(filtered_deps)
        return report
