# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of license-reporter package
- Support for multiple dependency file formats:
  - requirements.txt (and variants)
  - setup.py and setup.cfg
  - pyproject.toml (PEP 621 and Poetry formats)
  - Pipfile (Pipenv)
  - environment.yml (Conda)
- Multiple output formats:
  - Human-readable text
  - JSON for programmatic processing
  - Markdown for documentation
- Intelligent dependency classification:
  - Runtime dependencies
  - Development dependencies
  - Optional dependencies
  - Build-time tools
- Advanced filtering options:
  - Include/exclude development dependencies
  - Runtime-only mode for PyInstaller compliance
  - Pattern-based package exclusion
  - Build tool filtering
- License analysis features:
  - Automatic license detection
  - Attribution requirement analysis
  - Unknown license identification
- Comprehensive test suite with >95% coverage
- Complete API documentation and examples
- Command-line interface with extensive options
- Python API for programmatic use

### Changed
- Refactored monolithic script into modular package structure
- Improved error handling and user feedback
- Enhanced performance for large projects
- Better dependency type detection

### Fixed
- Improved parsing of complex dependency specifications
- Better handling of optional dependencies (toml, yaml)
- More robust file discovery and parsing

## [1.0.0] - 2024-01-XX

### Added
- Initial package release
- Core functionality for license reporting
- Support for major Python dependency formats
- Multiple output formats
- Comprehensive documentation
- Full test coverage

---

## Release Notes

### Version 1.0.0

This is the initial release of license-reporter, a comprehensive tool for analyzing Python project dependencies and generating license compliance reports.

**Key Features:**
- **Universal Compatibility**: Works with any Python project regardless of dependency management tool
- **Multiple Formats**: Supports requirements.txt, setup.py, pyproject.toml, Pipfile, and more
- **Flexible Output**: Generate reports in text, JSON, or Markdown format
- **Smart Filtering**: Runtime-only mode for PyInstaller, development dependency inclusion/exclusion
- **License Analysis**: Automatic license detection and attribution requirement analysis

**Use Cases:**
- Legal compliance for commercial software
- Open source license auditing
- PyInstaller bundle compliance
- Dependency analysis and documentation
- Security and supply chain analysis

**Installation:**
```bash
pip install license-reporter
```

**Quick Start:**
```bash
# Basic usage
license-reporter

# PyInstaller compliance
license-reporter --runtime-only --format text --output THIRD_PARTY_LICENSES.txt

# Complete analysis
license-reporter --all-deps --format json --output licenses.json
```

For detailed documentation, examples, and API reference, see the [README](README.md).
