"""
Tests for the parsers module.
"""

import pytest
from pathlib import Path

from license_reporter.parsers import DependencyParser
from license_reporter.core import DependencyInfo


class TestDependencyParser:
    """Tests for DependencyParser class."""

    def test_init(self, temp_project_dir):
        """Test parser initialization."""
        parser = DependencyParser(temp_project_dir)
        assert parser.project_root == temp_project_dir

    def test_discover_dependency_files_empty(self, temp_project_dir):
        """Test discovery with no dependency files."""
        parser = DependencyParser(temp_project_dir)
        files = parser.discover_dependency_files()
        assert files == {}

    def test_discover_dependency_files_requirements_txt(self, temp_project_dir, sample_requirements_txt):
        """Test discovery of requirements.txt."""
        parser = DependencyParser(temp_project_dir)
        files = parser.discover_dependency_files()
        
        assert "requirements.txt" in files
        assert files["requirements.txt"] == sample_requirements_txt

    def test_discover_dependency_files_multiple(self, temp_project_dir, sample_requirements_txt, 
                                               sample_dev_requirements_txt, sample_pyproject_toml):
        """Test discovery of multiple dependency files."""
        parser = DependencyParser(temp_project_dir)
        files = parser.discover_dependency_files()
        
        expected_files = {"requirements.txt", "dev-requirements.txt", "pyproject.toml"}
        assert set(files.keys()) == expected_files

    def test_determine_dep_type_from_filename_runtime(self):
        """Test dependency type determination for runtime files."""
        parser = DependencyParser(Path("."))
        
        assert parser._determine_dep_type_from_filename("requirements.txt") == "runtime"
        assert parser._determine_dep_type_from_filename("setup.py") == "runtime"

    def test_determine_dep_type_from_filename_dev(self):
        """Test dependency type determination for dev files."""
        parser = DependencyParser(Path("."))
        
        assert parser._determine_dep_type_from_filename("dev-requirements.txt") == "dev"
        assert parser._determine_dep_type_from_filename("requirements-dev.txt") == "dev"
        assert parser._determine_dep_type_from_filename("test-requirements.txt") == "dev"
        assert parser._determine_dep_type_from_filename("docs-requirements.txt") == "dev"

    def test_parse_requirements_txt_basic(self, temp_project_dir, sample_requirements_txt):
        """Test basic requirements.txt parsing."""
        parser = DependencyParser(temp_project_dir)
        deps = parser.parse_requirements_txt(sample_requirements_txt)
        
        # Should find the main dependencies
        dep_names = {dep.name for dep in deps}
        expected_names = {"requests", "click", "toml", "PyYAML", "packaging"}
        assert dep_names == expected_names
        
        # Check specific dependency details
        requests_dep = next(dep for dep in deps if dep.name == "requests")
        assert requests_dep.version_spec == ">=2.25.0"
        assert requests_dep.dep_type == "runtime"

    def test_parse_requirements_txt_dev_file(self, temp_project_dir, sample_dev_requirements_txt):
        """Test parsing dev requirements file."""
        parser = DependencyParser(temp_project_dir)
        deps = parser.parse_requirements_txt(sample_dev_requirements_txt)
        
        # All dependencies should be marked as dev
        for dep in deps:
            assert dep.dep_type == "dev"
        
        dep_names = {dep.name for dep in deps}
        expected_names = {"pytest", "pytest-cov", "black", "mypy"}
        assert dep_names == expected_names

    def test_parse_requirements_txt_comments_and_empty_lines(self, temp_project_dir):
        """Test that comments and empty lines are ignored."""
        requirements_content = """
# This is a comment
requests>=2.25.0

# Another comment
click>=8.0.0

"""
        requirements_file = temp_project_dir / "test-requirements.txt"
        requirements_file.write_text(requirements_content)
        
        parser = DependencyParser(temp_project_dir)
        deps = parser.parse_requirements_txt(requirements_file)
        
        assert len(deps) == 2
        dep_names = {dep.name for dep in deps}
        assert dep_names == {"requests", "click"}

    def test_parse_requirements_txt_pip_options(self, temp_project_dir):
        """Test that pip options are ignored."""
        requirements_content = """
-e git+https://github.com/user/repo.git#egg=package
--index-url https://pypi.org/simple/
requests>=2.25.0
-r other-requirements.txt
click>=8.0.0
"""
        requirements_file = temp_project_dir / "test-requirements.txt"
        requirements_file.write_text(requirements_content)
        
        parser = DependencyParser(temp_project_dir)
        deps = parser.parse_requirements_txt(requirements_file)
        
        # Should only find the regular package dependencies
        assert len(deps) == 2
        dep_names = {dep.name for dep in deps}
        assert dep_names == {"requests", "click"}

    def test_parse_setup_py_basic(self, temp_project_dir, sample_setup_py):
        """Test basic setup.py parsing."""
        parser = DependencyParser(temp_project_dir)
        deps = parser.parse_setup_py(sample_setup_py)
        
        # Should find install_requires dependencies
        runtime_deps = [dep for dep in deps if dep.dep_type == "runtime"]
        runtime_names = {dep.name for dep in runtime_deps}
        expected_runtime = {"requests", "click", "toml"}
        assert runtime_names == expected_runtime
        
        # Should find extras_require dependencies
        optional_deps = [dep for dep in deps if dep.dep_type == "optional"]
        assert len(optional_deps) > 0

    def test_parse_pyproject_toml_pep621(self, temp_project_dir, sample_pyproject_toml):
        """Test pyproject.toml parsing with PEP 621 format."""
        parser = DependencyParser(temp_project_dir)
        deps = parser.parse_pyproject_toml(sample_pyproject_toml)
        
        # Should find project dependencies
        runtime_deps = [dep for dep in deps if dep.dep_type == "runtime"]
        runtime_names = {dep.name for dep in runtime_deps}
        
        # From both [project.dependencies] and [tool.poetry.dependencies]
        assert "requests" in runtime_names
        assert "click" in runtime_names
        assert "toml" in runtime_names

    def test_parse_pyproject_toml_optional_dependencies(self, temp_project_dir, sample_pyproject_toml):
        """Test parsing optional dependencies from pyproject.toml."""
        parser = DependencyParser(temp_project_dir)
        deps = parser.parse_pyproject_toml(sample_pyproject_toml)
        
        # Should find dev dependencies
        dev_deps = [dep for dep in deps if dep.dep_type == "dev"]
        dev_names = {dep.name for dep in dev_deps}
        
        # From both [project.optional-dependencies] and [tool.poetry.dev-dependencies]
        assert "pytest" in dev_names
        assert "black" in dev_names
        assert "mypy" in dev_names

    def test_parse_pyproject_toml_no_toml_package(self, temp_project_dir, sample_pyproject_toml, monkeypatch):
        """Test pyproject.toml parsing when toml package is not available."""
        # Mock toml as None
        import license_reporter.parsers
        monkeypatch.setattr(license_reporter.parsers, "toml", None)
        
        parser = DependencyParser(temp_project_dir)
        deps = parser.parse_pyproject_toml(sample_pyproject_toml)
        
        # Should return empty list with warning
        assert deps == []

    def test_get_all_dependencies_multiple_files(self, temp_project_dir, sample_requirements_txt, 
                                                sample_dev_requirements_txt):
        """Test getting all dependencies from multiple files."""
        parser = DependencyParser(temp_project_dir)
        all_deps = parser.get_all_dependencies()
        
        # Should combine dependencies from both files
        dep_names = {dep.name for dep in all_deps}
        
        # From requirements.txt
        assert "requests" in dep_names
        assert "click" in dep_names
        
        # From dev-requirements.txt
        assert "pytest" in dep_names
        assert "black" in dep_names
        
        # Check dependency types
        runtime_deps = [dep for dep in all_deps if dep.dep_type == "runtime"]
        dev_deps = [dep for dep in all_deps if dep.dep_type == "dev"]
        
        assert len(runtime_deps) > 0
        assert len(dev_deps) > 0

    def test_get_all_dependencies_no_files(self, temp_project_dir):
        """Test getting dependencies when no dependency files exist."""
        parser = DependencyParser(temp_project_dir)
        all_deps = parser.get_all_dependencies()
        
        assert all_deps == []
