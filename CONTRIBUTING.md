# Contributing to License Reporter

Thank you for your interest in contributing to License Reporter! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic familiarity with Python packaging and dependency management

### Areas for Contribution

We welcome contributions in several areas:

- **Bug fixes**: Fix issues reported in GitHub Issues
- **New features**: Add support for new dependency formats or output options
- **Documentation**: Improve README, docstrings, or add examples
- **Testing**: Add test cases or improve test coverage
- **Performance**: Optimize parsing or report generation
- **Compatibility**: Add support for new Python versions or platforms

## Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/yourusername/license-reporter.git
   cd license-reporter
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e .[dev]
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

5. **Verify the setup:**
   ```bash
   pytest
   license-reporter --help
   ```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-conda-support`
- `fix/requirements-parsing-bug`
- `docs/improve-api-examples`
- `test/add-integration-tests`

### Commit Messages

Follow conventional commit format:
- `feat: add support for Conda environment.yml files`
- `fix: handle malformed requirements.txt lines`
- `docs: add API usage examples`
- `test: add tests for pyproject.toml parsing`
- `refactor: simplify dependency classification logic`

### Code Organization

The project follows a modular structure:

```
src/license_reporter/
├── __init__.py          # Package exports
├── core.py              # Main LicenseReporter class
├── parsers.py           # Dependency file parsers
├── formatters.py        # Output formatters
├── cli.py               # Command-line interface
└── __main__.py          # Module entry point

tests/
├── test_core.py         # Core functionality tests
├── test_parsers.py      # Parser tests
├── test_formatters.py   # Formatter tests
├── test_cli.py          # CLI tests
├── test_integration.py  # Integration tests
└── conftest.py          # Test fixtures
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=license_reporter --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run specific test
pytest tests/test_core.py::TestLicenseReporter::test_basic_functionality
```

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test complete workflows
3. **CLI Tests**: Test command-line interface
4. **Performance Tests**: Test with large projects (marked with `@pytest.mark.slow`)

### Writing Tests

- Use descriptive test names: `test_parse_requirements_txt_with_comments`
- Include both positive and negative test cases
- Test edge cases and error conditions
- Use fixtures for common test data
- Mock external dependencies when appropriate

### Test Coverage

Maintain >95% test coverage. Check coverage with:
```bash
pytest --cov=license_reporter --cov-report=term-missing
```

## Code Style

### Formatting and Linting

The project uses several tools for code quality:

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Lint code
flake8 src tests

# Type checking
mypy src

# Run all checks
pre-commit run --all-files
```

### Style Guidelines

- Follow PEP 8 for Python code style
- Use type hints for all public functions
- Write comprehensive docstrings for classes and functions
- Keep functions focused and reasonably sized
- Use meaningful variable and function names

### Documentation

- Add docstrings to all public classes and functions
- Use Google-style docstrings
- Include examples in docstrings when helpful
- Update README.md for user-facing changes
- Update CHANGELOG.md for all changes

## Submitting Changes

### Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write code following the style guidelines
   - Add or update tests
   - Update documentation

3. **Test your changes:**
   ```bash
   pytest
   pre-commit run --all-files
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request:**
   - Use a descriptive title
   - Explain what changes you made and why
   - Reference any related issues
   - Include screenshots for UI changes

### Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Include tests for new functionality
- Update documentation as needed
- Ensure all CI checks pass
- Respond to review feedback promptly

## Release Process

### Version Numbering

The project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version in `src/license_reporter/__init__.py`
2. Update CHANGELOG.md with release notes
3. Create and test the release build
4. Tag the release: `git tag v1.2.3`
5. Push tags: `git push --tags`
6. Create GitHub release with release notes
7. Publish to PyPI (maintainers only)

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bug Reports**: Open a GitHub Issue
- **Feature Requests**: Open a GitHub Issue with the "enhancement" label
- **Security Issues**: Email the maintainers directly

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for their contributions
- GitHub contributors list
- Release notes for significant contributions

Thank you for contributing to License Reporter!
