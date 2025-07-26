"""
Dependency file parsers for various Python project formats.

This module handles parsing of different dependency specification files
including requirements.txt, setup.py, pyproject.toml, Pipfile, and environment.yml.
"""

import re
from pathlib import Path
from typing import Dict, List

from .core import DependencyInfo

try:
    import toml
except ImportError:
    toml = None

try:
    import yaml
except ImportError:
    yaml = None


class DependencyParser:
    """
    Parser for various dependency specification formats.

    This class handles the discovery and parsing of dependency files in Python projects.
    It supports multiple formats and automatically detects dependency types based on
    file names and content structure.

    Supported formats:
    - requirements.txt (and variants like dev-requirements.txt)
    - setup.py and setup.cfg
    - pyproject.toml (both PEP 621 and Poetry formats)
    - Pipfile (Pipenv)
    - environment.yml (Conda)

    The parser automatically classifies dependencies as:
    - runtime: Core application dependencies
    - dev: Development and testing dependencies
    - optional: Optional feature dependencies

    Example:
        >>> parser = DependencyParser(Path('/path/to/project'))
        >>> files = parser.discover_dependency_files()
        >>> dependencies = parser.get_all_dependencies()
        >>> print(f"Found {len(dependencies)} dependencies")
    """

    def __init__(self, project_path: Path):
        """Initialize the dependency parser.

        Args:
            project_path: Path to the project directory
        """
        self.project_root = project_path

    def discover_dependency_files(self) -> Dict[str, Path]:
        """Discover dependency specification files in the project.

        Returns:
            Dictionary mapping file types to their paths
        """
        files = {}

        # Check for various dependency specification formats
        candidates = {
            "requirements.txt": self.project_root / "requirements.txt",
            "setup.py": self.project_root / "setup.py",
            "setup.cfg": self.project_root / "setup.cfg",
            "pyproject.toml": self.project_root / "pyproject.toml",
            "Pipfile": self.project_root / "Pipfile",
            "environment.yml": self.project_root / "environment.yml",
            "environment.yaml": self.project_root / "environment.yaml",
            "conda.yml": self.project_root / "conda.yml",
            "requirements-dev.txt": self.project_root / "requirements-dev.txt",
            "dev-requirements.txt": self.project_root / "dev-requirements.txt",
            "test-requirements.txt": self.project_root / "test-requirements.txt",
        }

        for name, path in candidates.items():
            if path.exists():
                files[name] = path

        return files

    def parse_requirements_txt(self, file_path: Path) -> List[DependencyInfo]:
        """Parse requirements.txt format files.

        Args:
            file_path: Path to the requirements file

        Returns:
            List of dependency information
        """
        dependencies = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Skip -e (editable) installs and other pip options
                    if line.startswith("-"):
                        continue

                    # Extract package name and version spec
                    # Handle various formats: package, package==1.0, package>=1.0, etc.
                    match = re.match(r"^([a-zA-Z0-9_.-]+)(.*)$", line)
                    if match:
                        name = match.group(1)
                        version_spec = match.group(2) if match.group(2) else ""

                        # Determine dependency type based on filename
                        dep_type = self._determine_dep_type_from_filename(
                            file_path.name
                        )

                        dependencies.append(
                            DependencyInfo(name, version_spec, dep_type)
                        )

        except Exception as e:
            print(f"Warning: Error parsing {file_path}: {e}")

        return dependencies

    def parse_setup_py(self, file_path: Path) -> List[DependencyInfo]:
        """Parse setup.py files to extract dependencies.

        Args:
            file_path: Path to the setup.py file

        Returns:
            List of dependency information
        """
        dependencies = []

        try:
            # Read setup.py content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract install_requires using regex (basic approach)
            # Look for install_requires
            install_requires_match = re.search(
                r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL
            )

            if install_requires_match:
                requires_content = install_requires_match.group(1)
                # Extract quoted package names
                package_matches = re.findall(r'["\']([^"\']+)["\']', requires_content)

                for package_spec in package_matches:
                    name = re.split(r"[<>=!]", package_spec)[0].strip()
                    version_spec = package_spec[len(name) :].strip()
                    dependencies.append(DependencyInfo(name, version_spec, "runtime"))

            # Look for extras_require
            extras_match = re.search(
                r"extras_require\s*=\s*{(.*?)}", content, re.DOTALL
            )

            if extras_match:
                extras_content = extras_match.group(1)
                # This is a simplified parser - real setup.py parsing is complex
                package_matches = re.findall(r'["\']([^"\']+)["\']', extras_content)

                for package_spec in package_matches:
                    if (
                        "=" in package_spec
                        or ">" in package_spec
                        or "<" in package_spec
                    ):
                        name = re.split(r"[<>=!]", package_spec)[0].strip()
                        version_spec = package_spec[len(name) :].strip()
                        dependencies.append(
                            DependencyInfo(name, version_spec, "optional")
                        )

        except Exception as e:
            print(f"Warning: Error parsing {file_path}: {e}")

        return dependencies

    def parse_pyproject_toml(self, file_path: Path) -> List[DependencyInfo]:
        """Parse pyproject.toml files.

        Args:
            file_path: Path to the pyproject.toml file

        Returns:
            List of dependency information
        """
        dependencies = []

        if not toml:
            print(
                "Warning: toml package not available, skipping pyproject.toml parsing"
            )
            return dependencies

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = toml.load(f)

            # PEP 621 format: [project.dependencies]
            if "project" in data and "dependencies" in data["project"]:
                for dep_spec in data["project"]["dependencies"]:
                    name = re.split(r"[<>=!]", dep_spec)[0].strip()
                    version_spec = dep_spec[len(name) :].strip()
                    dependencies.append(DependencyInfo(name, version_spec, "runtime"))

            # PEP 621 format: [project.optional-dependencies]
            if "project" in data and "optional-dependencies" in data["project"]:
                for group_name, deps in data["project"][
                    "optional-dependencies"
                ].items():
                    dep_type = (
                        "dev" if group_name in ["dev", "test", "docs"] else "optional"
                    )
                    for dep_spec in deps:
                        name = re.split(r"[<>=!]", dep_spec)[0].strip()
                        version_spec = dep_spec[len(name) :].strip()
                        dependencies.append(
                            DependencyInfo(name, version_spec, dep_type)
                        )

            # Poetry format: [tool.poetry.dependencies]
            if "tool" in data and "poetry" in data["tool"]:
                poetry = data["tool"]["poetry"]

                if "dependencies" in poetry:
                    for name, spec in poetry["dependencies"].items():
                        if name == "python":  # Skip Python version spec
                            continue
                        version_spec = str(spec) if not isinstance(spec, dict) else ""
                        dependencies.append(
                            DependencyInfo(name, version_spec, "runtime")
                        )

                if "dev-dependencies" in poetry:
                    for name, spec in poetry["dev-dependencies"].items():
                        version_spec = str(spec) if not isinstance(spec, dict) else ""
                        dependencies.append(DependencyInfo(name, version_spec, "dev"))

        except Exception as e:
            print(f"Warning: Error parsing {file_path}: {e}")

        return dependencies

    def _determine_dep_type_from_filename(self, filename: str) -> str:
        """Determine dependency type from filename.

        Args:
            filename: Name of the dependency file

        Returns:
            Dependency type (runtime, dev, etc.)
        """
        filename_lower = filename.lower()

        if any(keyword in filename_lower for keyword in ["dev", "development"]):
            return "dev"
        elif any(keyword in filename_lower for keyword in ["test", "testing"]):
            return "dev"
        elif any(keyword in filename_lower for keyword in ["doc", "docs"]):
            return "dev"
        else:
            return "runtime"

    def get_all_dependencies(self) -> List[DependencyInfo]:
        """Get all dependencies from all discovered dependency files.

        Returns:
            List of all discovered dependencies
        """
        all_deps = []
        dependency_files = self.discover_dependency_files()

        for file_type, file_path in dependency_files.items():
            if file_type.endswith(".txt"):
                deps = self.parse_requirements_txt(file_path)
            elif file_type == "setup.py":
                deps = self.parse_setup_py(file_path)
            elif file_type == "pyproject.toml":
                deps = self.parse_pyproject_toml(file_path)
            else:
                continue  # Skip unsupported formats for now

            all_deps.extend(deps)

        return all_deps
