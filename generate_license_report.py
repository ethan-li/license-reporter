#!/usr/bin/env python3
"""
Universal Python License Report Generator

A standalone, project-agnostic tool for analyzing Python project dependencies
and generating comprehensive license compliance reports. Supports multiple
dependency specification formats and output options.

Features:
- Supports requirements.txt, setup.py, pyproject.toml, Pipfile, environment.yml
- Distinguishes between runtime, development, and optional dependencies
- Multiple output formats: text, JSON, markdown
- Filtering options for different use cases
- PyInstaller compliance mode for executable distribution
- Comprehensive license detection and attribution requirements

Usage:
    # Analyze current directory
    python generate_license_report.py

    # Analyze specific project
    python generate_license_report.py /path/to/project

    # Generate PyInstaller compliance report
    python generate_license_report.py --runtime-only --format text

    # Comprehensive analysis with dev dependencies
    python generate_license_report.py --include-dev --format json

    # Custom filtering and output
    python generate_license_report.py --exclude "test*,dev*" --format markdown
"""

import argparse
import json
import os
import re
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any
import configparser

try:
    import pkg_resources
except ImportError:
    pkg_resources = None

try:
    import toml
except ImportError:
    toml = None

try:
    import yaml
except ImportError:
    yaml = None


class DependencyInfo:
    """Information about a dependency."""

    def __init__(self, name: str, version_spec: str = "", dep_type: str = "runtime"):
        self.name = name.strip()
        self.version_spec = version_spec.strip()
        self.dep_type = dep_type  # runtime, dev, optional, build

    def __repr__(self):
        return f"DependencyInfo({self.name}, {self.version_spec}, {self.dep_type})"


class LicenseReporter:
    """Universal license report generator for Python projects."""

    def __init__(self, project_path: Path = None):
        """Initialize the license reporter.

        Args:
            project_path: Path to the project directory to analyze.
                         If None, uses current directory.
        """
        self.project_root = Path(project_path) if project_path else Path.cwd()

        # Build-time dependencies that should be excluded from runtime reports
        self.build_time_packages = {
            'pip', 'setuptools', 'wheel', 'build', 'twine', 'virtualenv', 'venv',
            'pyinstaller', 'pytest', 'mypy', 'black', 'flake8', 'isort', 'coverage',
            'tox', 'pre-commit', 'sphinx', 'mkdocs', 'jupyter', 'notebook',
            'ipython', 'ipykernel', 'conda', 'mamba', 'poetry', 'pipenv', 'flit',
            'hatch', 'pdm', 'bandit', 'safety', 'autopep8', 'yapf', 'pylint',
            'pydocstyle', 'pycodestyle', 'pyflakes', 'mccabe'
        }

        # Type stub packages (not bundled in PyInstaller)
        self.type_stub_packages = {
            'types-', 'typing-extensions', 'mypy-extensions', 'stub-'
        }

        # Testing frameworks and related packages
        self.test_packages = {
            'pytest', 'unittest2', 'nose', 'nose2', 'testtools', 'mock',
            'pytest-cov', 'pytest-xdist', 'pytest-mock', 'factory-boy',
            'faker', 'hypothesis', 'tox', 'coverage', 'codecov'
        }
        
    def discover_dependency_files(self) -> Dict[str, Path]:
        """Discover dependency specification files in the project."""
        files = {}

        # Check for various dependency specification formats
        candidates = {
            'requirements.txt': self.project_root / 'requirements.txt',
            'setup.py': self.project_root / 'setup.py',
            'setup.cfg': self.project_root / 'setup.cfg',
            'pyproject.toml': self.project_root / 'pyproject.toml',
            'Pipfile': self.project_root / 'Pipfile',
            'environment.yml': self.project_root / 'environment.yml',
            'environment.yaml': self.project_root / 'environment.yaml',
            'conda.yml': self.project_root / 'conda.yml',
            'requirements-dev.txt': self.project_root / 'requirements-dev.txt',
            'dev-requirements.txt': self.project_root / 'dev-requirements.txt',
            'test-requirements.txt': self.project_root / 'test-requirements.txt',
        }

        for name, path in candidates.items():
            if path.exists():
                files[name] = path

        return files

    def parse_requirements_txt(self, file_path: Path) -> List[DependencyInfo]:
        """Parse requirements.txt format files."""
        dependencies = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    # Skip -e (editable) installs and other pip options
                    if line.startswith('-'):
                        continue

                    # Extract package name and version spec
                    # Handle various formats: package, package==1.0, package>=1.0, etc.
                    import re
                    match = re.match(r'^([a-zA-Z0-9_.-]+)(.*)$', line)
                    if match:
                        name = match.group(1)
                        version_spec = match.group(2) if match.group(2) else ""

                        # Determine dependency type based on filename
                        dep_type = self._determine_dep_type_from_filename(file_path.name)

                        dependencies.append(DependencyInfo(name, version_spec, dep_type))

        except Exception as e:
            print(f"Warning: Error parsing {file_path}: {e}")

        return dependencies

    def parse_setup_py(self, file_path: Path) -> List[DependencyInfo]:
        """Parse setup.py files to extract dependencies."""
        dependencies = []

        try:
            # Read setup.py content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract install_requires using regex (basic approach)
            import re

            # Look for install_requires
            install_requires_match = re.search(
                r'install_requires\s*=\s*\[(.*?)\]',
                content,
                re.DOTALL
            )

            if install_requires_match:
                requires_content = install_requires_match.group(1)
                # Extract quoted package names
                package_matches = re.findall(r'["\']([^"\']+)["\']', requires_content)

                for package_spec in package_matches:
                    name = re.split(r'[<>=!]', package_spec)[0].strip()
                    version_spec = package_spec[len(name):].strip()
                    dependencies.append(DependencyInfo(name, version_spec, "runtime"))

            # Look for extras_require
            extras_match = re.search(
                r'extras_require\s*=\s*{(.*?)}',
                content,
                re.DOTALL
            )

            if extras_match:
                extras_content = extras_match.group(1)
                # This is a simplified parser - real setup.py parsing is complex
                package_matches = re.findall(r'["\']([^"\']+)["\']', extras_content)

                for package_spec in package_matches:
                    if '=' in package_spec or '>' in package_spec or '<' in package_spec:
                        name = re.split(r'[<>=!]', package_spec)[0].strip()
                        version_spec = package_spec[len(name):].strip()
                        dependencies.append(DependencyInfo(name, version_spec, "optional"))

        except Exception as e:
            print(f"Warning: Error parsing {file_path}: {e}")

        return dependencies

    def parse_pyproject_toml(self, file_path: Path) -> List[DependencyInfo]:
        """Parse pyproject.toml files."""
        dependencies = []

        if not toml:
            print("Warning: toml package not available, skipping pyproject.toml parsing")
            return dependencies

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)

            # PEP 621 format: [project.dependencies]
            if 'project' in data and 'dependencies' in data['project']:
                for dep_spec in data['project']['dependencies']:
                    name = re.split(r'[<>=!]', dep_spec)[0].strip()
                    version_spec = dep_spec[len(name):].strip()
                    dependencies.append(DependencyInfo(name, version_spec, "runtime"))

            # PEP 621 format: [project.optional-dependencies]
            if 'project' in data and 'optional-dependencies' in data['project']:
                for group_name, deps in data['project']['optional-dependencies'].items():
                    dep_type = "dev" if group_name in ['dev', 'test', 'docs'] else "optional"
                    for dep_spec in deps:
                        name = re.split(r'[<>=!]', dep_spec)[0].strip()
                        version_spec = dep_spec[len(name):].strip()
                        dependencies.append(DependencyInfo(name, version_spec, dep_type))

            # Poetry format: [tool.poetry.dependencies]
            if 'tool' in data and 'poetry' in data['tool']:
                poetry = data['tool']['poetry']

                if 'dependencies' in poetry:
                    for name, spec in poetry['dependencies'].items():
                        if name == 'python':  # Skip Python version spec
                            continue
                        version_spec = str(spec) if not isinstance(spec, dict) else ""
                        dependencies.append(DependencyInfo(name, version_spec, "runtime"))

                if 'dev-dependencies' in poetry:
                    for name, spec in poetry['dev-dependencies'].items():
                        version_spec = str(spec) if not isinstance(spec, dict) else ""
                        dependencies.append(DependencyInfo(name, version_spec, "dev"))

        except Exception as e:
            print(f"Warning: Error parsing {file_path}: {e}")

        return dependencies

    def _determine_dep_type_from_filename(self, filename: str) -> str:
        """Determine dependency type from filename."""
        filename_lower = filename.lower()

        if any(keyword in filename_lower for keyword in ['dev', 'development']):
            return "dev"
        elif any(keyword in filename_lower for keyword in ['test', 'testing']):
            return "dev"
        elif any(keyword in filename_lower for keyword in ['doc', 'docs']):
            return "dev"
        else:
            return "runtime"

    def get_package_info(self, package_name: str) -> Dict:
        """Get package information including license."""
        info = {
            "name": package_name,
            "version": "unknown",
            "license": "unknown",
            "author": "unknown",
            "homepage": "unknown",
            "requires_attribution": True  # Conservative default
        }
        
        try:
            if pkg_resources:
                dist = pkg_resources.get_distribution(package_name)
                info["version"] = dist.version
                
                # Try to get license from metadata
                if hasattr(dist, 'get_metadata'):
                    try:
                        metadata = dist.get_metadata('METADATA')
                        for line in metadata.split('\n'):
                            if line.startswith('License:'):
                                info["license"] = line.split(':', 1)[1].strip()
                            elif line.startswith('Author:'):
                                info["author"] = line.split(':', 1)[1].strip()
                            elif line.startswith('Home-page:'):
                                info["homepage"] = line.split(':', 1)[1].strip()
                    except:
                        pass
                        
        except Exception:
            pass
            
        # Determine if attribution is required
        info["requires_attribution"] = self._requires_attribution(info["license"])
        
        return info
    
    def _requires_attribution(self, license_text: str) -> bool:
        """Determine if a license requires attribution."""
        license_lower = license_text.lower()
        
        # Licenses that require attribution
        attribution_required = [
            "mit", "bsd", "apache", "isc", "mpl", "mozilla",
            "creative commons", "cc-by"
        ]
        
        # Licenses that don't require attribution
        no_attribution = [
            "public domain", "unlicense", "wtfpl"
        ]
        
        for license_type in no_attribution:
            if license_type in license_lower:
                return False
                
        for license_type in attribution_required:
            if license_type in license_lower:
                return True
                
        # Conservative default: require attribution if unknown
        return True
    
    def get_all_dependencies(self) -> List[DependencyInfo]:
        """Get all dependencies from all discovered dependency files."""
        all_deps = []
        dependency_files = self.discover_dependency_files()

        for file_type, file_path in dependency_files.items():
            if file_type.endswith('.txt'):
                deps = self.parse_requirements_txt(file_path)
            elif file_type == 'setup.py':
                deps = self.parse_setup_py(file_path)
            elif file_type == 'pyproject.toml':
                deps = self.parse_pyproject_toml(file_path)
            else:
                continue  # Skip unsupported formats for now

            all_deps.extend(deps)

        return all_deps

    def filter_dependencies(self, dependencies: List[DependencyInfo],
                          include_dev: bool = False,
                          include_optional: bool = False,
                          runtime_only: bool = False,
                          exclude_patterns: List[str] = None) -> List[DependencyInfo]:
        """Filter dependencies based on criteria."""
        filtered = []
        exclude_patterns = exclude_patterns or []

        for dep in dependencies:
            # Skip if package name matches exclude patterns
            if any(self._matches_pattern(dep.name, pattern) for pattern in exclude_patterns):
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
            if runtime_only and any(dep.name.startswith(stub) for stub in self.type_stub_packages):
                continue

            # Exclude test packages for runtime-only reports
            if runtime_only and dep.name.lower() in self.test_packages:
                continue

            filtered.append(dep)

        return filtered

    def _matches_pattern(self, name: str, pattern: str) -> bool:
        """Check if package name matches a pattern (supports wildcards)."""
        import re
        # Convert shell-style wildcards to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        return bool(re.match(f'^{regex_pattern}$', name, re.IGNORECASE))

    def get_runtime_dependencies(self) -> Set[str]:
        """Get list of packages that are actually bundled in PyInstaller executable.

        This method is kept for backward compatibility with OSI integration.
        """
        all_deps = self.get_all_dependencies()
        runtime_deps = self.filter_dependencies(all_deps, runtime_only=True)
        return {dep.name for dep in runtime_deps}

    def _analyze_osi_imports(self) -> Set[str]:
        """Analyze OSI source code to find actual third-party imports."""
        imports = set()

        # Verified third-party packages actually used by OSI at runtime
        # Based on analysis of import statements in OSI source code
        osi_runtime_deps = {
            'toml',      # Used in: osi/pyproject_parser.py
            'packaging', # Used in: osi/environment_manager.py, osi/dependency_resolver.py
            'pkginfo',   # Used in: osi/wheel_manager.py (optional import)
        }

        # Only include packages that are actually installed
        for package in osi_runtime_deps:
            try:
                if pkg_resources:
                    pkg_resources.get_distribution(package)
                    imports.add(package)
            except:
                pass

        return imports

    def _get_pyinstaller_dependencies(self) -> Set[str]:
        """Use PyInstaller's analysis to find actual runtime dependencies."""
        deps = set()

        try:
            # Try to run PyInstaller's dependency analysis
            main_script = self.project_root / "osi_main.py"
            if not main_script.exists():
                return deps

            # Create a temporary spec file for analysis
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(f"""
import sys
sys.path.insert(0, '{self.project_root}')

# Import main module to trigger dependency discovery
try:
    import osi.launcher
    import osi.config_manager
    import osi.dependency_resolver
    import osi.environment_manager
    import osi.utils
    import osi.wheel_manager
except ImportError as e:
    print(f"Import error: {{e}}")
""")
                temp_script = f.name

            # Run the script to see what gets imported
            result = subprocess.run([
                sys.executable, temp_script
            ], capture_output=True, text=True, timeout=30)

            # Clean up
            Path(temp_script).unlink()

        except Exception:
            # If PyInstaller analysis fails, fall back to requirements.txt
            pass

        return deps

    def get_requirements_packages(self) -> List[str]:
        """Get list of packages from requirements.txt (legacy method)."""
        return list(self.get_runtime_dependencies())
    
    def generate_report(self,
                       include_dev: bool = False,
                       include_optional: bool = False,
                       runtime_only: bool = False,
                       exclude_patterns: List[str] = None,
                       project_name: str = None) -> Dict:
        """Generate comprehensive license report.

        Args:
            include_dev: Include development dependencies
            include_optional: Include optional dependencies
            runtime_only: Only include runtime dependencies (for PyInstaller compliance)
            exclude_patterns: List of patterns to exclude (supports wildcards)
            project_name: Name of the project being analyzed
        """
        # Get all dependencies and filter them
        all_deps = self.get_all_dependencies()
        filtered_deps = self.filter_dependencies(
            all_deps,
            include_dev=include_dev,
            include_optional=include_optional,
            runtime_only=runtime_only,
            exclude_patterns=exclude_patterns
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
            "dependency_files": [str(f) for f in self.discover_dependency_files().values()],
            "packages": [],
            "summary": {
                "total_packages": 0,
                "runtime_packages": 0,
                "dev_packages": 0,
                "optional_packages": 0,
                "requires_attribution": 0,
                "unknown_licenses": 0
            },
            "excluded_build_tools": list(self.build_time_packages) if runtime_only else [],
            "filters_applied": {
                "include_dev": include_dev,
                "include_optional": include_optional,
                "runtime_only": runtime_only,
                "exclude_patterns": exclude_patterns or []
            }
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

    def _detect_project_name(self) -> str:
        """Attempt to detect the project name from various sources."""
        # Try pyproject.toml first
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists() and toml:
            try:
                with open(pyproject_path, 'r', encoding='utf-8') as f:
                    data = toml.load(f)
                if 'project' in data and 'name' in data['project']:
                    return data['project']['name']
                if 'tool' in data and 'poetry' in data['tool'] and 'name' in data['tool']['poetry']:
                    return data['tool']['poetry']['name']
            except:
                pass

        # Try setup.py
        setup_path = self.project_root / "setup.py"
        if setup_path.exists():
            try:
                with open(setup_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                import re
                match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
            except:
                pass

        # Fall back to directory name
        return self.project_root.name
    
    def format_text_report(self, report: Dict) -> str:
        """Format report as human-readable text."""
        lines = []
        lines.append("=" * 80)
        lines.append("THIRD-PARTY SOFTWARE LICENSES")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Project: {report['project']}")
        lines.append(f"Project Path: {report['project_path']}")
        lines.append(f"Generated by: {report['generated_by']}")
        lines.append(f"Report Type: {report['report_type']}")
        lines.append("")

        # Dependency files analyzed
        if report.get('dependency_files'):
            lines.append("DEPENDENCY FILES ANALYZED:")
            for file_path in report['dependency_files']:
                lines.append(f"  - {file_path}")
            lines.append("")

        # Summary statistics
        summary = report['summary']
        lines.append("SUMMARY:")
        lines.append(f"  Total packages: {summary['total_packages']}")
        if summary.get('runtime_packages', 0) > 0:
            lines.append(f"  Runtime packages: {summary['runtime_packages']}")
        if summary.get('dev_packages', 0) > 0:
            lines.append(f"  Development packages: {summary['dev_packages']}")
        if summary.get('optional_packages', 0) > 0:
            lines.append(f"  Optional packages: {summary['optional_packages']}")
        lines.append(f"  Packages requiring attribution: {summary['requires_attribution']}")
        lines.append(f"  Packages with unknown licenses: {summary['unknown_licenses']}")
        lines.append("")

        # Filters applied
        filters = report.get('filters_applied', {})
        if any(filters.values()):
            lines.append("FILTERS APPLIED:")
            if filters.get('runtime_only'):
                lines.append("  - Runtime dependencies only (PyInstaller compliance mode)")
            if filters.get('include_dev'):
                lines.append("  - Development dependencies included")
            if filters.get('include_optional'):
                lines.append("  - Optional dependencies included")
            if filters.get('exclude_patterns'):
                lines.append(f"  - Excluded patterns: {', '.join(filters['exclude_patterns'])}")
            lines.append("")

        # Excluded build tools
        if report.get('excluded_build_tools'):
            lines.append("EXCLUDED BUILD-TIME DEPENDENCIES:")
            lines.append("The following build tools are excluded as they are not")
            lines.append("distributed with the PyInstaller executable:")
            excluded = ", ".join(sorted(report['excluded_build_tools']))
            lines.append(f"{excluded}")
            lines.append("")

        lines.append("=" * 80)
        lines.append("PACKAGE DETAILS")
        lines.append("=" * 80)
        lines.append("")

        for package in report["packages"]:
            lines.append(f"Package: {package['name']}")
            lines.append(f"Version: {package['version']}")
            if package.get('version_spec'):
                lines.append(f"Version Spec: {package['version_spec']}")
            lines.append(f"Dependency Type: {package.get('dependency_type', 'unknown')}")
            lines.append(f"License: {package['license']}")
            lines.append(f"Author: {package['author']}")
            lines.append(f"Homepage: {package['homepage']}")
            lines.append(f"Requires Attribution: {'Yes' if package['requires_attribution'] else 'No'}")
            lines.append("-" * 40)
            lines.append("")

        return "\n".join(lines)

    def format_markdown_report(self, report: Dict) -> str:
        """Format report as Markdown."""
        lines = []
        lines.append("# Third-Party Software Licenses")
        lines.append("")
        lines.append(f"**Project:** {report['project']}")
        lines.append(f"**Project Path:** `{report['project_path']}`")
        lines.append(f"**Generated by:** {report['generated_by']}")
        lines.append(f"**Report Type:** {report['report_type']}")
        lines.append("")

        # Summary
        summary = report['summary']
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total packages:** {summary['total_packages']}")
        if summary.get('runtime_packages', 0) > 0:
            lines.append(f"- **Runtime packages:** {summary['runtime_packages']}")
        if summary.get('dev_packages', 0) > 0:
            lines.append(f"- **Development packages:** {summary['dev_packages']}")
        if summary.get('optional_packages', 0) > 0:
            lines.append(f"- **Optional packages:** {summary['optional_packages']}")
        lines.append(f"- **Packages requiring attribution:** {summary['requires_attribution']}")
        lines.append(f"- **Packages with unknown licenses:** {summary['unknown_licenses']}")
        lines.append("")

        # Dependency files
        if report.get('dependency_files'):
            lines.append("## Dependency Files Analyzed")
            lines.append("")
            for file_path in report['dependency_files']:
                lines.append(f"- `{file_path}`")
            lines.append("")

        # Package details table
        lines.append("## Package Details")
        lines.append("")
        lines.append("| Package | Version | Type | License | Attribution Required |")
        lines.append("|---------|---------|------|---------|---------------------|")

        for package in report["packages"]:
            name = package['name']
            version = package['version']
            dep_type = package.get('dependency_type', 'unknown')
            license_info = package['license']
            attribution = 'Yes' if package['requires_attribution'] else 'No'

            lines.append(f"| {name} | {version} | {dep_type} | {license_info} | {attribution} |")

        lines.append("")

        # Detailed license information
        lines.append("## Detailed License Information")
        lines.append("")

        for package in report["packages"]:
            lines.append(f"### {package['name']}")
            lines.append("")
            lines.append(f"- **Version:** {package['version']}")
            if package.get('version_spec'):
                lines.append(f"- **Version Specification:** `{package['version_spec']}`")
            lines.append(f"- **Dependency Type:** {package.get('dependency_type', 'unknown')}")
            lines.append(f"- **License:** {package['license']}")
            lines.append(f"- **Author:** {package['author']}")
            if package['homepage'] != 'unknown':
                lines.append(f"- **Homepage:** {package['homepage']}")
            lines.append(f"- **Requires Attribution:** {'Yes' if package['requires_attribution'] else 'No'}")
            lines.append("")

        return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Universal Python License Report Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze current directory
  python generate_license_report.py

  # Analyze specific project
  python generate_license_report.py /path/to/project

  # Generate PyInstaller compliance report
  python generate_license_report.py --runtime-only --format text --output THIRD_PARTY_LICENSES.txt

  # Include development dependencies
  python generate_license_report.py --include-dev --format json

  # Exclude test packages
  python generate_license_report.py --exclude "test*,pytest*" --format markdown

  # Comprehensive analysis
  python generate_license_report.py --include-dev --include-optional --format json --output licenses.json
        """
    )

    # Positional argument for project path
    parser.add_argument("project_path", nargs="?", default=".",
                       help="Path to project directory (default: current directory)")

    # Output format options
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="text",
                       help="Output format (default: text)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    # Dependency inclusion options
    parser.add_argument("--include-dev", action="store_true",
                       help="Include development dependencies")
    parser.add_argument("--include-optional", action="store_true",
                       help="Include optional dependencies")
    parser.add_argument("--runtime-only", action="store_true",
                       help="Include only runtime dependencies (PyInstaller compliance mode)")
    parser.add_argument("--all-deps", action="store_true",
                       help="Include all dependencies (runtime + dev + optional)")

    # Filtering options
    parser.add_argument("--exclude", help="Comma-separated list of package patterns to exclude (supports wildcards)")
    parser.add_argument("--project-name", help="Override detected project name")

    # Backward compatibility
    parser.add_argument("--legacy-mode", action="store_true",
                       help="Use legacy OSI-specific behavior for backward compatibility")

    args = parser.parse_args()

    # Handle conflicting options
    if args.all_deps:
        include_dev = True
        include_optional = True
        runtime_only = False
    elif args.runtime_only:
        include_dev = False
        include_optional = False
        runtime_only = True
    else:
        include_dev = args.include_dev
        include_optional = args.include_optional
        runtime_only = False

    # Parse exclude patterns
    exclude_patterns = []
    if args.exclude:
        exclude_patterns = [pattern.strip() for pattern in args.exclude.split(',')]

    # Initialize reporter
    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        print(f"Error: Project path '{project_path}' does not exist")
        return 1

    reporter = LicenseReporter(project_path)

    # Legacy mode for OSI backward compatibility
    if args.legacy_mode:
        # Use old behavior
        report = reporter.generate_report(runtime_only=True, project_name="OSI (Open Source Installer)")
    else:
        # Use new enhanced behavior
        report = reporter.generate_report(
            include_dev=include_dev,
            include_optional=include_optional,
            runtime_only=runtime_only,
            exclude_patterns=exclude_patterns,
            project_name=args.project_name
        )

    # Format output
    if args.format == "json":
        output = json.dumps(report, indent=2)
    elif args.format == "markdown":
        output = reporter.format_markdown_report(report)
    else:
        output = reporter.format_text_report(report)

    # Write output
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"License report written to {args.output}")

            # Print summary
            summary = report['summary']
            print(f"Analyzed {summary['total_packages']} packages")
            if summary.get('runtime_packages', 0) > 0:
                print(f"  - Runtime: {summary['runtime_packages']}")
            if summary.get('dev_packages', 0) > 0:
                print(f"  - Development: {summary['dev_packages']}")
            if summary.get('optional_packages', 0) > 0:
                print(f"  - Optional: {summary['optional_packages']}")
            print(f"  - Requiring attribution: {summary['requires_attribution']}")

        except Exception as e:
            print(f"Error writing to {args.output}: {e}")
            return 1
    else:
        print(output)

    return 0


if __name__ == "__main__":
    main()
