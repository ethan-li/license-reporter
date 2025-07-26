"""
Pytest configuration and fixtures for license_reporter tests.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_requirements_txt(temp_project_dir):
    """Create a sample requirements.txt file."""
    requirements_content = """
# Production dependencies
requests>=2.25.0
click>=8.0.0
toml>=0.10.0

# Comments and empty lines should be ignored

PyYAML>=5.1.0
packaging>=20.0
"""
    requirements_file = temp_project_dir / "requirements.txt"
    requirements_file.write_text(requirements_content)
    return requirements_file


@pytest.fixture
def sample_dev_requirements_txt(temp_project_dir):
    """Create a sample dev-requirements.txt file."""
    dev_requirements_content = """
pytest>=7.0.0
pytest-cov>=4.0.0
black>=22.0.0
mypy>=1.0.0
"""
    dev_requirements_file = temp_project_dir / "dev-requirements.txt"
    dev_requirements_file.write_text(dev_requirements_content)
    return dev_requirements_file


@pytest.fixture
def sample_pyproject_toml(temp_project_dir):
    """Create a sample pyproject.toml file."""
    pyproject_content = """
[project]
name = "test-project"
version = "1.0.0"
dependencies = [
    "requests>=2.25.0",
    "click>=8.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=22.0.0"
]
docs = [
    "sphinx>=5.0.0"
]

[tool.poetry.dependencies]
python = "^3.8"
toml = "^0.10.0"

[tool.poetry.dev-dependencies]
mypy = "^1.0.0"
"""
    pyproject_file = temp_project_dir / "pyproject.toml"
    pyproject_file.write_text(pyproject_content)
    return pyproject_file


@pytest.fixture
def sample_setup_py(temp_project_dir):
    """Create a sample setup.py file."""
    setup_content = """
from setuptools import setup, find_packages

setup(
    name="test-project",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "click>=8.0.0",
        "toml>=0.10.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0"
        ],
        "docs": [
            "sphinx>=5.0.0"
        ]
    }
)
"""
    setup_file = temp_project_dir / "setup.py"
    setup_file.write_text(setup_content)
    return setup_file


@pytest.fixture
def sample_report_data():
    """Sample report data for testing formatters."""
    return {
        "project": "test-project",
        "project_path": "/path/to/project",
        "generated_by": "Universal Python License Reporter",
        "report_type": "Runtime Dependencies",
        "dependency_files": ["/path/to/requirements.txt"],
        "packages": [
            {
                "name": "requests",
                "version": "2.28.1",
                "version_spec": ">=2.25.0",
                "dependency_type": "runtime",
                "license": "Apache Software License",
                "author": "Kenneth Reitz",
                "homepage": "https://requests.readthedocs.io",
                "requires_attribution": True,
            },
            {
                "name": "click",
                "version": "8.1.3",
                "version_spec": ">=8.0.0",
                "dependency_type": "runtime",
                "license": "BSD License",
                "author": "Pallets",
                "homepage": "https://palletsprojects.com/p/click/",
                "requires_attribution": True,
            },
        ],
        "summary": {
            "total_packages": 2,
            "runtime_packages": 2,
            "dev_packages": 0,
            "optional_packages": 0,
            "requires_attribution": 2,
            "unknown_licenses": 0,
        },
        "excluded_build_tools": [],
        "filters_applied": {
            "include_dev": False,
            "include_optional": False,
            "runtime_only": False,
            "exclude_patterns": [],
        },
    }
