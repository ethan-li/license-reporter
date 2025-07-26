"""
Command-line interface for the license reporter.

This module provides the main CLI entry point and argument parsing.
"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import LicenseReporter
from .formatters import get_formatter


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command-line argument parser.

    This function sets up all command-line options and arguments for the license
    reporter tool, including output formats, dependency filtering options, and
    various analysis modes.

    Returns:
        Configured ArgumentParser instance with all options defined

    Example:
        >>> parser = create_parser()
        >>> args = parser.parse_args(['--format', 'json', '/path/to/project'])
        >>> print(args.format)
        'json'
    """
    parser = argparse.ArgumentParser(
        description="Universal Python License Report Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze current directory
  license-reporter

  # Analyze specific project
  license-reporter /path/to/project

  # Generate PyInstaller compliance report
  license-reporter --runtime-only --format text --output THIRD_PARTY_LICENSES.txt

  # Include development dependencies
  license-reporter --include-dev --format json

  # Exclude test packages
  license-reporter --exclude "test*,pytest*" --format markdown

  # Comprehensive analysis
  license-reporter --include-dev --include-optional --format json --output licenses.json
        """
    )

    # Version argument
    parser.add_argument("--version", action="version", version=f"license-reporter {__version__}")

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

    return parser


def main() -> int:
    """Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = create_parser()
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

    try:
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
        formatter = get_formatter(args.format)
        output = formatter.format(report)

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

    except Exception as e:
        print(f"Error generating license report: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
