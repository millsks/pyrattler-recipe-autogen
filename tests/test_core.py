"""
Tests for pyrattler_recipe_autogen package.
"""

# Add src to path for testing
import os
import pathlib
import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from pyrattler_recipe_autogen.core import (
    _get_relative_path,
    _merge_dict,
    _normalize_deps,
    _toml_get,
    _warn,
    assemble_recipe,
    build_about_section,
    build_build_section,
    build_context_section,
    build_extra_section,
    build_package_section,
    build_requirements_section,
    build_source_section,
    build_test_section,
    generate_recipe,
    load_pyproject_toml,
    resolve_dynamic_version,
    write_recipe_yaml,
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


def test_toml_get():
    """Test nested TOML key lookup utility."""
    data = {"a": {"b": {"c": "value"}}, "simple": "test"}

    assert _toml_get(data, "a.b.c") == "value"
    assert _toml_get(data, "simple") == "test"
    assert _toml_get(data, "nonexistent") is None
    assert _toml_get(data, "nonexistent", "default") == "default"
    assert _toml_get(data, "a.b.missing") is None
    assert _toml_get({}, "a.b.c") is None


def test_merge_dict():
    """Test dictionary merging utility."""
    base = {"a": 1, "b": 2}
    extra = {"b": 3, "c": 4}

    result = _merge_dict(base, extra)
    assert result == {"a": 1, "b": 3, "c": 4}

    # Test with None extra
    result = _merge_dict(base, None)
    assert result == base

    # Test that original base dict is not modified
    assert base == {"a": 1, "b": 2}


def test_get_relative_path():
    """Test relative path calculation utility."""
    # Test file within recipe directory
    result = _get_relative_path("/home/user/project/file.txt", "/home/user/project")
    assert result == "file.txt"

    # Test file in subdirectory - normalize for cross-platform compatibility
    result = _get_relative_path("/home/user/project/sub/file.txt", "/home/user/project")
    expected = str(pathlib.Path("sub/file.txt"))
    assert result == expected

    # Test file outside recipe directory (should use ../)
    result = _get_relative_path("/home/user/file.txt", "/home/user/project")
    expected = str(pathlib.Path("../file.txt"))
    assert result == expected


def test_warn(capsys):
    """Test warning function."""
    _warn("Test warning message")
    captured = capsys.readouterr()
    assert "⚠ Test warning message" in captured.err


def test_load_pyproject_toml():
    """Test loading a simple pyproject.toml file."""
    toml_content = """
[project]
name = "test-package"
version = "0.1.0"
description = "Test package"
"""

    # Use mkstemp for better cross-platform compatibility
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


def test_load_pyproject_toml_missing_file():
    """Test loading non-existent pyproject.toml file."""
    nonexistent_path = pathlib.Path("nonexistent.toml")
    with pytest.raises(FileNotFoundError):
        load_pyproject_toml(nonexistent_path)


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


def test_build_context_section_dynamic_version():
    """Test building context section with dynamic version."""
    toml_data = {
        "project": {
            "name": "test-package",
            "dynamic": ["version"],
            "requires-python": ">=3.9",
        },
        "build-system": {"build-backend": "setuptools_scm.build_meta"},
    }

    with patch("pyrattler_recipe_autogen.core.resolve_dynamic_version") as mock_resolve:
        mock_resolve.return_value = "1.0.0dev"
        context = build_context_section(toml_data, pathlib.Path("."))

    assert context["version"] == "1.0.0dev"
    assert context["python_min"] == "3.9"
    assert "python_max" not in context  # Should not be present when not specified


def test_build_context_section_extra_context():
    """Test building context section with extra context overrides."""
    toml_data = {
        "project": {
            "name": "test-package",
            "version": "1.0.0",
        },
        "tool": {
            "conda": {
                "recipe": {
                    "extra_context": {
                        "python_min": "3.10",
                        "custom_var": "custom_value",
                    }
                }
            }
        },
    }

    context = build_context_section(toml_data, pathlib.Path("."))
    assert context["python_min"] == "3.10"  # Override from extra_context
    assert context["custom_var"] == "custom_value"


def test_build_context_section_missing_version():
    """Test error when version is missing and not dynamic."""
    toml_data = {
        "project": {
            "name": "test-package",
        }
    }

    with pytest.raises(ValueError, match="Version not found"):
        build_context_section(toml_data, pathlib.Path("."))


def test_build_package_section():
    """Test building package section."""
    toml_data = {"project": {"name": "test", "version": "1.0"}}
    result = build_package_section(toml_data, pathlib.Path("."))
    assert result == {"name": "${{ name }}", "version": "${{ version }}"}


def test_build_about_section_basic():
    """Test building about section with basic project info."""
    toml_data = {
        "project": {
            "name": "test-package",
            "description": "A test package",
            "urls": {
                "Homepage": "https://example.com",
                "Repository": "https://github.com/user/repo",
            },
            "license": {"text": "MIT"},
        }
    }

    result = build_about_section(toml_data, pathlib.Path("."))
    assert result["summary"] == "A test package"
    assert result["license"] == "MIT"
    assert result["homepage"] == "https://example.com"
    assert result["repository"] == "https://github.com/user/repo"


def test_build_about_section_license_file():
    """Test building about section with license file."""
    # Create a temporary license file
    fd, temp_path = tempfile.mkstemp(suffix=".txt", text=True)
    license_path = pathlib.Path(temp_path)

    try:
        with os.fdopen(fd, "w") as f:
            f.write("MIT License\n\nCopyright (c) 2023\n")

        toml_data = {
            "project": {"name": "test-package", "license": {"file": str(license_path)}}
        }

        result = build_about_section(toml_data, pathlib.Path("."))
        assert result["license"] == "MIT"
        assert result["license_file"] == license_path.name
    finally:
        try:
            license_path.unlink()
        except (OSError, PermissionError):
            pass


def test_build_about_section_license_files_list():
    """Test building about section with multiple license files."""
    toml_data = {
        "project": {
            "name": "test-package",
            "license-files": ["LICENSE", "COPYING"],
            "license": "MIT",
        }
    }

    result = build_about_section(toml_data, pathlib.Path("."))
    assert result["license_file"] == ["LICENSE", "COPYING"]


def test_build_source_section():
    """Test building source section."""
    toml_data = {}
    result = build_source_section(toml_data)
    assert result == {"path": ".."}  # Default value

    # Test with custom source configuration
    toml_data = {
        "tool": {
            "conda": {
                "recipe": {"source": {"url": "https://example.com/package.tar.gz"}}
            }
        }
    }
    result = build_source_section(toml_data)
    assert result == {"url": "https://example.com/package.tar.gz"}


def test_build_build_section():
    """Test building build section."""
    toml_data = {}
    result = build_build_section(toml_data)
    assert result["script"] == "$PYTHON -m pip install . -vv --no-build-isolation"
    assert result["number"] == 0

    # Test with custom build configuration
    toml_data = {
        "tool": {
            "conda": {
                "recipe": {
                    "build": {
                        "script": "custom script",
                        "number": 5,
                        "noarch": "python",
                    }
                }
            }
        }
    }
    result = build_build_section(toml_data)
    assert result["script"] == "custom script"
    assert result["number"] == 5
    assert result["noarch"] == "python"


def test_build_requirements_section_basic():
    """Test building requirements section with basic dependencies."""
    toml_data = {"project": {"dependencies": ["numpy>=1.0", "pandas"]}}
    context = {"python_min": "3.8", "python_max": "4.0"}

    result = build_requirements_section(toml_data, context)
    assert "python >=3.8,<4.0" in result["run"]
    assert "numpy>=1.0" in result["run"]
    assert "pandas" in result["run"]


def test_build_requirements_section_pixi():
    """Test building requirements section with pixi configuration."""
    toml_data = {
        "project": {"dependencies": ["requests"]},
        "tool": {
            "pixi": {
                "feature": {"build": {"dependencies": {"cmake": ">=3.20"}}},
                "host-dependencies": {"python": ">=3.8", "pip": "*"},
            }
        },
    }
    context = {"python_min": "3.8"}

    result = build_requirements_section(toml_data, context)
    assert "cmake>=3.20" in result["build"]
    assert "python >=3.8" in result["host"]
    assert "pip" in result["host"]


def test_build_test_section():
    """Test building test section."""
    assert build_test_section({}) is None

    toml_data = {
        "tool": {
            "conda": {
                "recipe": {
                    "test": {"imports": ["mypackage"], "commands": ["mypackage --help"]}
                }
            }
        }
    }

    result = build_test_section(toml_data)
    assert result["imports"] == ["mypackage"]
    assert result["commands"] == ["mypackage --help"]


def test_build_extra_section():
    """Test building extra section."""
    assert build_extra_section({}) is None

    toml_data = {
        "tool": {"conda": {"recipe": {"extra": {"recipe-maintainers": ["username"]}}}}
    }

    result = build_extra_section(toml_data)
    assert result["recipe-maintainers"] == ["username"]


def test_assemble_recipe():
    """Test assembling complete recipe."""
    toml_data = {
        "project": {
            "name": "test-package",
            "version": "1.0.0",
            "description": "Test package",
            "dependencies": ["numpy"],
        }
    }

    result = assemble_recipe(toml_data, pathlib.Path("."), pathlib.Path("."))

    assert "context" in result
    assert "package" in result
    assert "source" in result
    assert "build" in result
    assert "requirements" in result
    assert "about" in result
    assert result["context"]["name"] == "test-package"
    assert result["package"]["name"] == "${{ name }}"


def test_write_recipe_yaml():
    """Test writing recipe to YAML file."""
    recipe_dict = {
        "context": {"name": "test", "version": "1.0"},
        "package": {"name": "${{ name }}", "version": "${{ version }}"},
    }

    fd, temp_path = tempfile.mkstemp(suffix=".yaml", text=True)
    output_path = pathlib.Path(temp_path)

    try:
        os.close(fd)  # Close the file descriptor so we can write to it
        write_recipe_yaml(recipe_dict, output_path, overwrite=True)

        # Verify the file was written
        assert output_path.exists()
        content = output_path.read_text()
        assert "context:" in content
        assert "name: test" in content
    finally:
        try:
            output_path.unlink()
        except (OSError, PermissionError):
            pass


def test_write_recipe_yaml_backup_existing():
    """Test writing recipe with backup of existing file."""
    recipe_dict = {"test": "data"}

    fd, temp_path = tempfile.mkstemp(suffix=".yaml", text=True)
    output_path = pathlib.Path(temp_path)

    try:
        # Write initial content
        with os.fdopen(fd, "w") as f:
            f.write("existing content")

        # Write new content without overwrite (should backup)
        write_recipe_yaml(recipe_dict, output_path, overwrite=False)

        # Verify backup was created
        backup_path = output_path.with_suffix(output_path.suffix + ".bak")
        assert backup_path.exists()
        assert backup_path.read_text() == "existing content"

        # Verify new content was written
        content = output_path.read_text()
        assert "test: data" in content

        # Clean up backup
        backup_path.unlink()
    finally:
        try:
            output_path.unlink()
        except (OSError, PermissionError):
            pass


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


def test_resolve_dynamic_version_setuptools_scm():
    """Test dynamic version resolution with setuptools_scm."""
    toml_data = {"build-system": {"build-backend": "setuptools_scm.build_meta"}}

    # Mock the setuptools_scm import within the function
    mock_scm = MagicMock()
    mock_scm.get_version.return_value = "1.2.3dev"

    with patch("builtins.__import__") as mock_import:

        def side_effect(name, *args, **kwargs):
            if name == "setuptools_scm":
                return mock_scm
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect
        result = resolve_dynamic_version(pathlib.Path("."), toml_data)
        assert result == "1.2.3dev"


def test_resolve_dynamic_version_setuptools_scm_subprocess():
    """Test dynamic version resolution with setuptools_scm via subprocess."""
    toml_data = {"tool": {"setuptools_scm": {}}}

    # Mock setuptools_scm import to fail and trigger subprocess fallback
    with patch("builtins.__import__") as mock_import:

        def side_effect(name, *args, **kwargs):
            if name == "setuptools_scm":
                raise ImportError("setuptools_scm not available")
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="4.5.6", returncode=0)
            result = resolve_dynamic_version(pathlib.Path("."), toml_data)
            assert result == "4.5.6"


def test_resolve_dynamic_version_setuptools_scm_exception():
    """Test dynamic version resolution when setuptools_scm raises an exception."""
    toml_data = {"build-system": {"build-backend": "setuptools_scm.build_meta"}}

    # Mock setuptools_scm to raise an exception
    mock_scm = MagicMock()
    mock_scm.get_version.side_effect = Exception("Version resolution failed")

    with patch("builtins.__import__") as mock_import:

        def side_effect(name, *args, **kwargs):
            if name == "setuptools_scm":
                return mock_scm
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "1.2.3\n"
            mock_run.return_value.returncode = 0

            result = resolve_dynamic_version(pathlib.Path("."), toml_data)
            assert result == "1.2.3"


def test_resolve_dynamic_version_hatchling():
    """Test dynamic version resolution with hatchling."""
    toml_data = {"build-system": {"build-backend": "hatchling.build"}}

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "2.0.0\n"
        mock_run.return_value.returncode = 0

        result = resolve_dynamic_version(pathlib.Path("."), toml_data)
        assert result == "2.0.0"


def test_resolve_dynamic_version_poetry():
    """Test dynamic version resolution with poetry."""
    toml_data = {"build-system": {"build-backend": "poetry.core.masonry.api"}}

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "3.0.0\n"
        mock_run.return_value.returncode = 0

        result = resolve_dynamic_version(pathlib.Path("."), toml_data)
        assert result == "3.0.0"


def test_resolve_dynamic_version_unknown_backend(capsys):
    """Test dynamic version resolution with unknown backend falls back to placeholder."""
    toml_data = {"build-system": {"build-backend": "unknown.backend"}}

    result = resolve_dynamic_version(pathlib.Path("."), toml_data)
    assert result == "${{ env.get('PYPROJECT_VERSION', default='0.1.0') }}"

    # Should emit warning about using placeholder
    captured = capsys.readouterr()
    assert "Could not resolve dynamic version" in captured.err


def test_resolve_dynamic_version_all_fail(capsys):
    """Test dynamic version resolution when all methods fail."""
    toml_data = {"build-system": {"build-backend": "unknown.backend"}}

    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd")):
        result = resolve_dynamic_version(pathlib.Path("."), toml_data)

    # Should return environment variable placeholder
    assert result == "${{ env.get('PYPROJECT_VERSION', default='0.1.0') }}"

    # Should emit warning
    captured = capsys.readouterr()
    assert "Could not resolve dynamic version" in captured.err


def test_build_context_section_version_conflict_warning(capsys):
    """Test warning when version is both dynamic and present."""
    toml_data = {
        "project": {
            "name": "test-package",
            "version": "1.0.0",  # Present in project
            "dynamic": ["version"],  # But also marked as dynamic
        }
    }

    with patch("pyrattler_recipe_autogen.core.resolve_dynamic_version") as mock_resolve:
        mock_resolve.return_value = "1.0.0dev"
        build_context_section(toml_data, pathlib.Path("."))

    captured = capsys.readouterr()
    assert "Version is marked as dynamic but also present" in captured.err


def test_build_requirements_section_no_pixi_warning(capsys):
    """Test warning when pixi configuration is not found."""
    toml_data = {"project": {"dependencies": ["numpy"]}}
    context = {"python_min": "3.8"}

    build_requirements_section(toml_data, context)

    captured = capsys.readouterr()
    assert "Pixi configuration not found" in captured.err


def test_build_requirements_section_with_overrides():
    """Test requirements section with recipe-specific overrides."""
    toml_data = {
        "project": {"dependencies": ["numpy"]},
        "tool": {
            "conda": {
                "recipe": {
                    "requirements": {
                        "build": ["cmake"],
                        "host": ["cython"],
                        "run": ["scipy"],
                    }
                }
            }
        },
    }
    context = {"python_min": "3.8"}

    result = build_requirements_section(toml_data, context)

    # Should have default empty lists plus overrides
    assert "cmake" in result["build"]
    assert "cython" in result["host"]
    assert "scipy" in result["run"]
    assert "numpy" in result["run"]  # From project dependencies


def test_build_requirements_section_python_versions():
    """Test different python version specifications."""
    toml_data = {"project": {"dependencies": []}}

    # Test with both min and max
    context = {"python_min": "3.8", "python_max": "4.0"}
    result = build_requirements_section(toml_data, context)
    assert "python >=3.8,<4.0" in result["run"]

    # Test with only min
    context = {"python_min": "3.9"}
    result = build_requirements_section(toml_data, context)
    assert "python >=3.9" in result["run"]

    # Test with no version constraints
    context = {}
    result = build_requirements_section(toml_data, context)
    assert "python" in result["run"]


def test_build_about_section_license_detection():
    """Test license detection from different license texts."""
    # Test Apache license detection
    fd, temp_path = tempfile.mkstemp(suffix=".txt", text=True)
    license_path = pathlib.Path(temp_path)

    test_cases = [
        ("Apache License\nVersion 2.0", "Apache-2.0"),
        ("BSD License", "BSD-3-Clause"),
        ("GNU GENERAL PUBLIC LICENSE\nVersion 3", "GPL-3.0"),
        ("GNU GENERAL PUBLIC LICENSE\nVersion 2", "GPL-2.0"),
        ("Unknown license text", None),
    ]

    for license_text, expected in test_cases:
        try:
            with os.fdopen(fd, "w") as f:
                f.write(license_text)

            # Re-open file descriptor for each test
            fd, temp_path = tempfile.mkstemp(suffix=".txt", text=True)
            license_path = pathlib.Path(temp_path)

            with license_path.open("w") as f:
                f.write(license_text)

            toml_data = {
                "project": {
                    "name": "test-package",
                    "license": {"file": str(license_path)},
                }
            }

            result = build_about_section(toml_data, pathlib.Path("."))
            assert result["license"] == expected

        finally:
            try:
                license_path.unlink()
            except (OSError, PermissionError):
                pass


def test_build_about_section_unreadable_license_file():
    """Test handling of unreadable license file."""
    toml_data = {
        "project": {
            "name": "test-package",
            "license": {"file": "/nonexistent/path/LICENSE"},
        }
    }

    result = build_about_section(toml_data, pathlib.Path("."))
    assert result["license"] is None  # Should not crash, just return None


def test_build_about_section_with_overrides():
    """Test about section with overrides from tool.conda.recipe.about."""
    toml_data = {
        "project": {
            "name": "test-package",
            "description": "Original description",
        },
        "tool": {
            "conda": {
                "recipe": {
                    "about": {
                        "summary": "Override description",
                        "dev_url": "https://dev.example.com",
                    }
                }
            }
        },
    }

    result = build_about_section(toml_data, pathlib.Path("."))
    assert result["summary"] == "Override description"  # Should be overridden
    assert result["dev_url"] == "https://dev.example.com"  # Should be added


def test_assemble_recipe_with_optional_sections():
    """Test assembling recipe with optional test and extra sections."""
    toml_data = {
        "project": {
            "name": "test-package",
            "version": "1.0.0",
            "description": "Test package",
        },
        "tool": {
            "conda": {
                "recipe": {
                    "test": {"imports": ["test_package"]},
                    "extra": {"recipe-maintainers": ["maintainer"]},
                }
            }
        },
    }

    result = assemble_recipe(toml_data, pathlib.Path("."), pathlib.Path("."))

    assert "test" in result
    assert result["test"]["imports"] == ["test_package"]
    assert "extra" in result
    assert result["extra"]["recipe-maintainers"] == ["maintainer"]


def test_get_relative_path_edge_cases():
    """Test edge cases for relative path calculation."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = pathlib.Path(tmpdir)

        # Test same directory
        result = _get_relative_path(tmpdir_path / "file.txt", tmpdir_path)
        assert result == "file.txt"

        # Test parent directory
        parent_dir = tmpdir_path.parent
        result = _get_relative_path(tmpdir_path / "file.txt", parent_dir)
        assert tmpdir_path.name in result
        assert "file.txt" in result


def test_get_relative_path_windows_cross_drive():
    """Test Windows cross-drive path handling."""
    # Mock os.path.commonpath to raise ValueError (simulating cross-drive scenario)
    with patch("pyrattler_recipe_autogen.core.os.path.commonpath") as mock_commonpath:
        mock_commonpath.side_effect = ValueError("Paths don't have the same drive")

        # Should fallback to absolute path when commonpath fails
        result = _get_relative_path("C:/project/file.txt", "D:/recipes")
        # Should return the absolute path as fallback
        assert "C:" in result or result == "C:/project/file.txt"


if __name__ == "__main__":
    pytest.main([__file__])
