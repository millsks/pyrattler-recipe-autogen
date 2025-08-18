"""
Tests for pyrattler_recipe_autogen package.
"""

import pathlib

# Add src to path for testing
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from pyrattler_recipe_autogen.core import (
    _normalize_deps,
    build_context_section,
    generate_recipe,
    load_pyproject_toml,
)


def test_normalize_deps_dict():
    """Test dependency normalization from dict format."""
    deps = {"numpy": ">=1.0", "scipy": "*", "pandas": ""}
    result = _normalize_deps(deps)
    expected = ["numpy>=1.0", "scipy", "pandas"]
    assert result == expected


def test_normalize_deps_list():
    """Test dependency normalization from list format."""
    deps = ["numpy>=1.0", "scipy", "pandas"]
    result = _normalize_deps(deps)
    assert result == deps


def test_normalize_deps_empty():
    """Test dependency normalization with empty input."""
    assert _normalize_deps([]) == []
    assert _normalize_deps({}) == []
    assert _normalize_deps(None) == []


def test_load_pyproject_toml():
    """Test loading a simple pyproject.toml file."""
    toml_content = """
[project]
name = "test-package"
version = "0.1.0"
description = "Test package"
"""

    # Use mkstemp for better cross-platform compatibility
    import os

    fd, temp_path = tempfile.mkstemp(suffix=".toml", text=True)
    toml_path = pathlib.Path(temp_path)

    try:
        # Write content and close file descriptor
        with os.fdopen(fd, "w") as f:
            f.write(toml_content)

        # Now load and test
        data = load_pyproject_toml(toml_path)
        assert data["project"]["name"] == "test-package"
        assert data["project"]["version"] == "0.1.0"
    finally:
        # Clean up the temporary file
        try:
            toml_path.unlink()
        except (OSError, PermissionError):
            # On Windows, sometimes the file is still locked
            # This is acceptable for a test cleanup
            pass


def test_build_context_section():
    """Test building context section from TOML data."""
    toml_data = {
        "project": {
            "name": "Test Package",
            "version": "1.2.3",
            "requires-python": ">=3.8,<4.0",
        }
    }

    context = build_context_section(toml_data, pathlib.Path("."))

    assert context["name"] == "test-package"  # lowercase and hyphenated
    assert context["version"] == "1.2.3"
    assert context["python_min"] == "3.8"
    assert context["python_max"] == "4.0"


@patch("pyrattler_recipe_autogen.core.write_recipe_yaml")
@patch("pyrattler_recipe_autogen.core.load_pyproject_toml")
def test_generate_recipe(mock_load, mock_write):
    """Test the main generate_recipe function."""
    # Mock the TOML loading
    mock_toml_data = {
        "project": {
            "name": "test-package",
            "version": "0.1.0",
            "description": "Test package",
            "dependencies": ["pyyaml"],
        }
    }
    mock_load.return_value = mock_toml_data

    # Call the function
    pyproject_path = pathlib.Path("pyproject.toml")
    output_path = pathlib.Path("recipe.yaml")
    generate_recipe(pyproject_path, output_path)

    # Verify the calls
    mock_load.assert_called_once_with(pyproject_path)
    mock_write.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
