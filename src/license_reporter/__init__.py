"""
License Reporter - Universal Python License Report Generator

A comprehensive tool for analyzing Python project dependencies and generating
license compliance reports. Supports multiple dependency specification formats
and output options.

Features:
- Supports requirements.txt, setup.py, pyproject.toml, Pipfile, environment.yml
- Distinguishes between runtime, development, and optional dependencies
- Multiple output formats: text, JSON, markdown
- Filtering options for different use cases
- PyInstaller compliance mode for executable distribution
- Comprehensive license detection and attribution requirements
"""

__version__ = "1.0.1"
__author__ = "Ethan Li"

from .cli import main
from .core import DependencyInfo, LicenseReporter
from .formatters import JSONFormatter, MarkdownFormatter, TextFormatter
from .parsers import DependencyParser

__all__ = [
    "LicenseReporter",
    "DependencyInfo",
    "DependencyParser",
    "TextFormatter",
    "JSONFormatter",
    "MarkdownFormatter",
    "main",
]
