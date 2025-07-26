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

__version__ = "1.0.0"
__author__ = "License Reporter Contributors"
__email__ = "license-reporter@example.com"

from .core import LicenseReporter, DependencyInfo
from .parsers import DependencyParser
from .formatters import TextFormatter, JSONFormatter, MarkdownFormatter
from .cli import main

__all__ = [
    "LicenseReporter",
    "DependencyInfo", 
    "DependencyParser",
    "TextFormatter",
    "JSONFormatter", 
    "MarkdownFormatter",
    "main",
]
