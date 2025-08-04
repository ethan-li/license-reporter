# License Reporter

[![PyPI version](https://badge.fury.io/py/license-reporter.svg)](https://badge.fury.io/py/license-reporter)
[![Python Support](https://img.shields.io/pypi/pyversions/license-reporter.svg)](https://pypi.org/project/license-reporter/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/yourusername/license-reporter/workflows/Tests/badge.svg)](https://github.com/yourusername/license-reporter/actions)
[![Coverage](https://codecov.io/gh/yourusername/license-reporter/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/license-reporter)

A comprehensive, project-agnostic tool for analyzing Python project dependencies and generating license compliance reports. Perfect for legal compliance, security audits, and understanding your project's dependency landscape.

## Features

- **Universal Compatibility**: Supports multiple dependency specification formats:
  - `requirements.txt` (and variants like `dev-requirements.txt`)
  - `setup.py` and `setup.cfg`
  - `pyproject.toml` (PEP 621 and Poetry formats)
  - `Pipfile` (Pipenv)
  - `environment.yml` (Conda)

- **Intelligent Dependency Classification**: Automatically distinguishes between:
  - Runtime dependencies
  - Development dependencies
  - Optional dependencies
  - Build-time tools

- **Multiple Output Formats**: Generate reports in:
  - Human-readable text
  - JSON for programmatic processing
  - Markdown for documentation

- **Smart Deduplication**:
  - Automatically removes duplicate packages from multiple dependency files
  - Preserves the most specific version constraints
  - Prioritizes runtime dependencies over development dependencies
  - Maintains transparency about dependency sources

- **Advanced Filtering**:
  - Include/exclude development dependencies
  - Runtime-only mode for PyInstaller compliance
  - Pattern-based package exclusion
  - Build tool filtering

- **License Analysis**:
  - Automatic license detection
  - Attribution requirement analysis
  - Unknown license identification

## Installation

### From PyPI (Recommended)

```bash
pip install license-reporter
```

### From Source

```bash
git clone https://github.com/yourusername/license-reporter.git
cd license-reporter
pip install -e .
```

### With Optional Dependencies

For enhanced functionality with YAML files:

```bash
pip install license-reporter[enhanced]
```

**Note**: TOML support is now included by default since `pyproject.toml` is the standard for modern Python projects.

For development:

```bash
pip install license-reporter[dev]
```

## Quick Start

### Basic Usage

```bash
# Analyze current directory
license-reporter

# Analyze specific project
license-reporter /path/to/project

# Generate JSON report
license-reporter --format json --output licenses.json
```

### Common Use Cases

#### PyInstaller Compliance Report

Generate a report of only the packages that will be bundled with your PyInstaller executable:

```bash
license-reporter --runtime-only --format text --output THIRD_PARTY_LICENSES.txt
```

#### Complete Project Analysis

Include all dependencies (runtime, development, and optional):

```bash
license-reporter --all-deps --format markdown --output LICENSE_REPORT.md
```

#### Exclude Test Dependencies

```bash
license-reporter --exclude "test*,pytest*,mock*" --format json
```

## Command Line Options

```
usage: license-reporter [-h] [--format {text,json,markdown}] [--output OUTPUT]
                        [--include-dev] [--include-optional] [--runtime-only]
                        [--all-deps] [--exclude EXCLUDE] [--project-name PROJECT_NAME]
                        [--legacy-mode]
                        [project_path]

positional arguments:
  project_path          Path to project directory (default: current directory)

optional arguments:
  -h, --help            show this help message and exit
  --format {text,json,markdown}
                        Output format (default: text)
  --output OUTPUT, -o OUTPUT
                        Output file (default: stdout)
  --include-dev         Include development dependencies
  --include-optional    Include optional dependencies
  --runtime-only        Include only runtime dependencies (PyInstaller compliance mode)
  --all-deps            Include all dependencies (runtime + dev + optional)
  --exclude EXCLUDE     Comma-separated list of package patterns to exclude (supports wildcards)
  --project-name PROJECT_NAME
                        Override detected project name
  --legacy-mode         Use legacy OSI-specific behavior for backward compatibility
```

## Python API

### Basic Usage

```python
from license_reporter import LicenseReporter

# Create reporter for current directory
reporter = LicenseReporter()

# Generate report
report = reporter.generate_report(
    include_dev=True,
    runtime_only=False,
    exclude_patterns=["test*"]
)

# Access report data
print(f"Found {report['summary']['total_packages']} packages")
for package in report['packages']:
    print(f"{package['name']}: {package['license']}")
```

### Advanced Usage

```python
from pathlib import Path
from license_reporter import LicenseReporter
from license_reporter.formatters import get_formatter

# Analyze specific project
project_path = Path("/path/to/project")
reporter = LicenseReporter(project_path)

# Generate comprehensive report
report = reporter.generate_report(
    include_dev=True,
    include_optional=True,
    exclude_patterns=["*test*", "dev-*"],
    project_name="My Project"
)

# Format as Markdown
formatter = get_formatter("markdown")
markdown_output = formatter.format(report)

# Save to file
with open("LICENSE_REPORT.md", "w") as f:
    f.write(markdown_output)
```

## Report Structure

The generated reports include:

- **Project Information**: Name, path, analysis type
- **Summary Statistics**: Package counts, attribution requirements
- **Dependency Files**: List of analyzed files
- **Package Details**: For each dependency:
  - Name and version
  - License information
  - Author and homepage
  - Attribution requirements
  - Dependency type (runtime/dev/optional)

## Smart Deduplication

When your project has multiple dependency files (e.g., both `requirements.txt` and `pyproject.toml`), License Reporter automatically deduplicates packages that appear in multiple files. The deduplication logic:

1. **Combines packages from all sources**: Analyzes all discovered dependency files
2. **Removes duplicates by package name**: Case-insensitive matching
3. **Preserves the most specific version**: Prioritizes exact versions (`==`) over ranges (`>=`)
4. **Maintains dependency type priority**: Runtime dependencies take precedence over dev/optional
5. **Tracks source information**: Reports which files were analyzed

### Example

If you have:
- `requirements.txt`: `requests>=2.25.0`
- `pyproject.toml`: `requests>=2.30.0`

The final report will contain only one `requests` entry with version `>=2.30.0` (the more restrictive constraint).

## Supported File Formats

### requirements.txt
```
requests>=2.25.0
click>=8.0.0
# Comments are ignored
-e git+https://github.com/user/repo.git#egg=package  # Ignored
```

### pyproject.toml (PEP 621)
```toml
[project]
dependencies = [
    "requests>=2.25.0",
    "click>=8.0.0"
]

[project.optional-dependencies]
dev = ["pytest>=7.0.0"]
```

### pyproject.toml (Poetry)
```toml
[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.25.0"

[tool.poetry.dev-dependencies]
pytest = "^7.0.0"
```

### setup.py
```python
setup(
    name="my-project",
    install_requires=[
        "requests>=2.25.0",
        "click>=8.0.0"
    ],
    extras_require={
        "dev": ["pytest>=7.0.0"]
    }
)
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
git clone https://github.com/yourusername/license-reporter.git
cd license-reporter
pip install -e .[dev]
pre-commit install
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
black src tests
isort src tests
flake8 src tests
mypy src
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a history of changes.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/license-reporter/issues)
- **Documentation**: [Read the Docs](https://license-reporter.readthedocs.io)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/license-reporter/discussions)
