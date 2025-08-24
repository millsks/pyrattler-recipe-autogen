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


def test_build_context_section_platform_variants():
    """Test platform/variant detection in context section."""
    toml_data = {
        "project": {
            "name": "test-package",
            "version": "1.0.0",
            "requires-python": ">=3.8,<4.0",
            "classifiers": [
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Operating System :: Microsoft :: Windows",
                "Operating System :: POSIX :: Linux",
            ],
            "dependencies": [
                "numpy>=1.20.0",
                "pywin32>=200; sys_platform == 'win32'",
                "some-package>=1.0; platform_machine == 'x86_64'",
            ],
        }
    }

    context = build_context_section(toml_data, pathlib.Path("."))

    # Check basic context
    assert context["name"] == "test-package"
    assert context["python_min"] == "3.8"
    assert context["python_max"] == "4.0"

    # Check platform variants
    assert "python_variants" in context
    assert "3.8" in context["python_variants"]
    assert "3.9" in context["python_variants"]
    assert "3.10" in context["python_variants"]

    # Check platform dependencies
    assert "platform_dependencies" in context
    platform_deps = context["platform_dependencies"]
    assert "win" in platform_deps
    assert "pywin32>=200" in platform_deps["win"]
    assert "arch_64" in platform_deps
    assert "some-package>=1.0" in platform_deps["arch_64"]

    # Check OS configuration
    assert "supported_platforms" in context
    supported = context["supported_platforms"]
    assert "win" in supported
    assert "linux" in supported


def test_detect_python_variants_from_classifiers():
    """Test Python version detection from classifiers."""
    from pyrattler_recipe_autogen.core import _detect_python_variants

    project = {
        "classifiers": [
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Development Status :: 4 - Beta",  # Should be ignored
        ]
    }

    variants = _detect_python_variants(project)
    assert variants == ["3.8", "3.9", "3.10"]


def test_detect_python_variants_from_requires():
    """Test Python version detection from requires-python."""
    from pyrattler_recipe_autogen.core import _detect_python_variants

    project = {"requires-python": ">=3.8,<3.12"}
    variants = _detect_python_variants(project)
    expected = ["3.8", "3.9", "3.10", "3.11"]
    assert variants == expected

    # Test single constraint
    project = {"requires-python": ">=3.9"}
    variants = _detect_python_variants(project)
    # Should generate reasonable range
    assert "3.9" in variants
    assert "3.10" in variants


def test_detect_platform_dependencies():
    """Test platform-specific dependency detection."""
    from pyrattler_recipe_autogen.core import _detect_platform_dependencies

    project = {
        "dependencies": [
            "numpy>=1.20.0",  # No marker
            "pywin32>=200; sys_platform == 'win32'",
            "some-linux-lib; sys_platform == 'linux'",
            "arch-specific; platform_machine == 'x86_64'",
            "arm-specific; platform_machine == 'aarch64'",
        ]
    }

    platform_deps = _detect_platform_dependencies(project)

    assert "win" in platform_deps
    assert "pywin32>=200" in platform_deps["win"]

    assert "linux" in platform_deps
    assert "some-linux-lib" in platform_deps["linux"]

    assert "arch_64" in platform_deps
    assert "arch-specific" in platform_deps["arch_64"]

    assert "arch_arm64" in platform_deps
    assert "arm-specific" in platform_deps["arch_arm64"]


def test_extract_platform_from_marker():
    """Test platform extraction from environment markers."""
    from pyrattler_recipe_autogen.core import _extract_platform_from_marker

    test_cases = [
        ('sys_platform == "win32"', "win"),
        ('sys_platform == "darwin"', "osx"),
        ('sys_platform == "linux"', "linux"),
        ("sys_platform == 'win32'", "win"),  # Single quotes
        ('python_version >= "3.8"', None),  # Not a platform marker
    ]

    for marker, expected in test_cases:
        result = _extract_platform_from_marker(marker)
        assert result == expected, f"Expected {marker} -> {expected}, got {result}"


def test_extract_architecture_from_marker():
    """Test architecture extraction from environment markers."""
    from pyrattler_recipe_autogen.core import _extract_architecture_from_marker

    test_cases = [
        ('platform_machine == "x86_64"', "64"),
        ('platform_machine == "amd64"', "64"),
        ('platform_machine == "aarch64"', "arm64"),
        ('platform_machine == "arm64"', "arm64"),
        ('platform_machine == "i386"', "32"),
        ('sys_platform == "win32"', None),  # Not an architecture marker
    ]

    for marker, expected in test_cases:
        result = _extract_architecture_from_marker(marker)
        assert result == expected, f"Expected {marker} -> {expected}, got {result}"


def test_detect_architecture_config():
    """Test architecture configuration detection."""
    from pyrattler_recipe_autogen.core import _detect_architecture_config

    # Test noarch detection for pure Python
    toml_data = {
        "build-system": {"build-backend": "flit_core.buildapi"},
        "project": {"dependencies": ["requests", "click"]},
    }
    config = _detect_architecture_config(toml_data)
    assert config["noarch"] == "python"

    # Test compiled dependency detection
    toml_data = {
        "build-system": {"build-backend": "setuptools.build_meta"},
        "project": {"dependencies": ["numpy>=1.20.0", "scipy"]},
    }
    config = _detect_architecture_config(toml_data)
    assert "arch_variants" in config
    assert config["arch_variants"] == ["64", "arm64"]


def test_detect_os_config():
    """Test OS configuration detection."""
    from pyrattler_recipe_autogen.core import _detect_os_config

    project = {
        "classifiers": [
            "Operating System :: Microsoft :: Windows",
            "Operating System :: POSIX :: Linux",
            "Operating System :: MacOS",
        ],
        "urls": {
            "Repository": "https://github.com/user/repo",
            "Windows-Installer": "https://example.com/windows-installer.exe",
            "Mac-Binary": "https://example.com/macos-binary.dmg",
        },
    }

    config = _detect_os_config(project)

    assert "supported_platforms" in config
    supported = config["supported_platforms"]
    assert "win" in supported
    assert "linux" in supported
    assert "osx" in supported

    assert config["has_windows_specific"] is True
    assert config["has_macos_specific"] is True


def test_parse_dependency_marker():
    """Test dependency marker parsing."""
    from pyrattler_recipe_autogen.core import _parse_dependency_marker

    # Test platform marker
    result = _parse_dependency_marker('pywin32>=200; sys_platform == "win32"')
    assert result == ("win", "pywin32>=200")

    # Test architecture marker
    result = _parse_dependency_marker('some-lib; platform_machine == "x86_64"')
    assert result == ("arch_64", "some-lib")

    # Test unsupported marker
    result = _parse_dependency_marker('some-lib; python_version >= "3.8"')
    assert result is None

    # Test no marker
    result = _parse_dependency_marker("numpy>=1.20.0")
    assert result is None


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


def test_build_source_section_git_detection():
    """Test auto-detection of Git repository sources."""
    toml_data = {
        "project": {
            "name": "test-package",
            "urls": {"Repository": "https://github.com/user/repo"},
        }
    }

    with patch("pyrattler_recipe_autogen.core._detect_git_ref") as mock_git_ref:
        mock_git_ref.return_value = None
        result = build_source_section(toml_data)

    assert result["git"] == "https://github.com/user/repo"
    assert "tag" not in result
    assert "branch" not in result


def test_build_source_section_git_with_tag():
    """Test Git source detection with tag."""
    toml_data = {
        "project": {
            "name": "test-package",
            "urls": {"Repository": "https://github.com/user/repo.git"},
        }
    }

    with patch("pyrattler_recipe_autogen.core._detect_git_ref") as mock_git_ref:
        mock_git_ref.return_value = "v1.2.3"
        result = build_source_section(toml_data)

    assert result["git"] == "https://github.com/user/repo"
    assert result["tag"] == "v1.2.3"


def test_build_source_section_git_ssh_conversion():
    """Test conversion of SSH Git URLs to HTTPS."""
    toml_data = {
        "project": {
            "name": "test-package",
            "urls": {"Repository": "git@github.com:user/repo.git"},
        }
    }

    with patch("pyrattler_recipe_autogen.core._detect_git_ref") as mock_git_ref:
        mock_git_ref.return_value = None
        result = build_source_section(toml_data)

    assert result["git"] == "https://github.com/user/repo"


def test_build_source_section_pypi_detection():
    """Test auto-detection of PyPI sources."""
    toml_data = {"project": {"name": "my-awesome-package", "version": "1.2.3"}}

    result = build_source_section(toml_data)
    expected_url = "https://pypi.org/packages/source/m/my-awesome-package/my_awesome_package-1.2.3.tar.gz"
    assert result["url"] == expected_url


def test_build_source_section_pypi_dynamic_version():
    """Test PyPI source with dynamic version."""
    toml_data = {"project": {"name": "test-package", "dynamic": ["version"]}}

    result = build_source_section(toml_data)
    expected_url = "https://pypi.org/packages/source/t/test-package/test_package-${{ version }}.tar.gz"
    assert result["url"] == expected_url


def test_build_source_section_url_detection():
    """Test detection of archive URLs."""
    toml_data = {
        "project": {
            "name": "test-package",
            "urls": {"Download": "https://example.com/package-1.0.0.tar.gz"},
        }
    }

    result = build_source_section(toml_data)
    assert result["url"] == "https://example.com/package-1.0.0.tar.gz"


def test_detect_git_source_various_platforms():
    """Test Git source detection for various platforms."""
    from pyrattler_recipe_autogen.core import _detect_git_source

    test_cases = [
        {"repository": "https://github.com/user/repo"},
        {"repository": "https://gitlab.com/user/repo"},
        {"repository": "https://bitbucket.org/user/repo"},
        {"repository": "git@github.com:user/repo.git"},
        {"homepage": "https://github.com/user/repo"},
    ]

    for urls in test_cases:
        with patch("pyrattler_recipe_autogen.core._detect_git_ref") as mock_git_ref:
            mock_git_ref.return_value = None
            result = _detect_git_source(urls)
        assert result is not None
        assert "git" in result


def test_is_git_url():
    """Test Git URL detection."""
    from pyrattler_recipe_autogen.core import _is_git_url

    git_urls = [
        "https://github.com/user/repo",
        "https://gitlab.com/user/repo",
        "git@github.com:user/repo.git",
        "https://bitbucket.org/user/repo",
        "https://sourceforge.net/p/project/git",
    ]

    non_git_urls = [
        "https://example.com",
        "https://pypi.org/project/package",
        "https://docs.python.org",
    ]

    for url in git_urls:
        assert _is_git_url(url), f"Expected {url} to be detected as Git URL"

    for url in non_git_urls:
        assert not _is_git_url(url), f"Expected {url} to NOT be detected as Git URL"


def test_normalize_git_url():
    """Test Git URL normalization."""
    from pyrattler_recipe_autogen.core import _normalize_git_url

    test_cases = [
        ("git@github.com:user/repo.git", "https://github.com/user/repo"),
        ("git@gitlab.com:user/repo.git", "https://gitlab.com/user/repo"),
        ("https://github.com/user/repo.git", "https://github.com/user/repo"),
        ("https://github.com/user/repo/", "https://github.com/user/repo"),
        ("https://github.com/user/repo", "https://github.com/user/repo"),
    ]

    for input_url, expected in test_cases:
        result = _normalize_git_url(input_url)
        assert result == expected, f"Expected {input_url} -> {expected}, got {result}"


def test_detect_git_ref():
    """Test Git reference detection."""
    from pyrattler_recipe_autogen.core import _detect_git_ref

    # Test tag detection
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "v1.2.3\n"
        result = _detect_git_ref()
        assert result == "v1.2.3"

    # Test branch detection when tag fails
    with patch("subprocess.run") as mock_run:

        def side_effect(*args, **kwargs):
            if "describe" in args[0]:
                mock_result = MagicMock()
                mock_result.returncode = 1
                return mock_result
            elif "branch" in args[0]:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "feature-branch\n"
                return mock_result

        mock_run.side_effect = side_effect
        result = _detect_git_ref()
        assert result == "feature-branch"

    # Test main/master branch filtering
    with patch("subprocess.run") as mock_run:

        def side_effect(*args, **kwargs):
            if "describe" in args[0]:
                mock_result = MagicMock()
                mock_result.returncode = 1
                return mock_result
            elif "branch" in args[0]:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "main\n"
                return mock_result

        mock_run.side_effect = side_effect
        result = _detect_git_ref()
        assert result is None  # main branch should be filtered out


def test_detect_pypi_source():
    """Test PyPI source detection."""
    from pyrattler_recipe_autogen.core import _detect_pypi_source

    # Test with static version
    project = {"name": "my-package", "version": "1.0.0"}
    result = _detect_pypi_source(project)
    expected_url = (
        "https://pypi.org/packages/source/m/my-package/my_package-1.0.0.tar.gz"
    )
    assert result["url"] == expected_url

    # Test with dynamic version
    project = {"name": "test-pkg", "dynamic": ["version"]}
    result = _detect_pypi_source(project)
    expected_url = (
        "https://pypi.org/packages/source/t/test-pkg/test_pkg-${{ version }}.tar.gz"
    )
    assert result["url"] == expected_url

    # Test with missing name
    project = {"version": "1.0.0"}
    result = _detect_pypi_source(project)
    assert result is None


def test_is_archive_url():
    """Test archive URL detection."""
    from pyrattler_recipe_autogen.core import _is_archive_url

    archive_urls = [
        "https://example.com/package.tar.gz",
        "https://example.com/package.tar.bz2",
        "https://example.com/package.tar.xz",
        "https://example.com/package.zip",
        "https://example.com/package.whl",
    ]

    non_archive_urls = [
        "https://example.com",
        "https://github.com/user/repo",
        "https://example.com/page.html",
    ]

    for url in archive_urls:
        assert _is_archive_url(url), f"Expected {url} to be detected as archive URL"

    for url in non_archive_urls:
        assert not _is_archive_url(
            url
        ), f"Expected {url} to NOT be detected as archive URL"


def test_build_source_section_priority():
    """Test source detection priority (Git > PyPI > URL > Path)."""
    # Git should take priority over PyPI
    toml_data = {
        "project": {
            "name": "test-package",
            "version": "1.0.0",
            "urls": {"Repository": "https://github.com/user/repo"},
        }
    }

    with patch("pyrattler_recipe_autogen.core._detect_git_ref") as mock_git_ref:
        mock_git_ref.return_value = None
        result = build_source_section(toml_data)

    assert "git" in result
    assert "url" not in result

    # PyPI should take priority over generic URL
    toml_data = {
        "project": {
            "name": "test-package",
            "version": "1.0.0",
            "urls": {"Download": "https://example.com/some-file.tar.gz"},
        }
    }

    result = build_source_section(toml_data)
    assert result["url"].startswith("https://pypi.org/packages/source")


def test_build_source_section_explicit_override():
    """Test that explicit configuration overrides auto-detection."""
    toml_data = {
        "project": {
            "name": "test-package",
            "urls": {"Repository": "https://github.com/user/repo"},
        },
        "tool": {
            "conda": {
                "recipe": {"source": {"url": "https://custom.com/package.tar.gz"}}
            }
        },
    }

    result = build_source_section(toml_data)
    assert result == {"url": "https://custom.com/package.tar.gz"}
    # Should not auto-detect Git source when explicit config is present


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


def test_build_build_section_poetry_backend():
    """Test build section with poetry backend auto-detection."""
    toml_data = {"build-system": {"build-backend": "poetry.core.masonry.api"}}
    result = build_build_section(toml_data)
    assert result["script"] == "poetry build && $PYTHON -m pip install dist/*.whl -vv"


def test_build_build_section_flit_backend():
    """Test build section with flit backend auto-detection."""
    toml_data = {"build-system": {"build-backend": "flit_core.buildapi"}}
    result = build_build_section(toml_data)
    assert result["script"] == "$PYTHON -m flit install"


def test_build_build_section_hatchling_backend():
    """Test build section with hatchling backend auto-detection."""
    toml_data = {"build-system": {"build-backend": "hatchling.build"}}
    result = build_build_section(toml_data)
    assert result["script"] == "$PYTHON -m pip install . -vv --no-build-isolation"


def test_build_build_section_entry_points():
    """Test build section with entry points auto-detection."""
    toml_data = {
        "project": {
            "scripts": {"my-cli": "mypackage.cli:main", "my-tool": "mypackage.tool:run"}
        }
    }
    result = build_build_section(toml_data)
    assert result["entry_points"] == [
        "my-cli = mypackage.cli:main",
        "my-tool = mypackage.tool:run",
    ]


def test_build_build_section_skip_conditions():
    """Test build section with skip conditions auto-detection."""
    # Test minimum Python version only
    toml_data = {"project": {"requires-python": ">=3.9"}}
    result = build_build_section(toml_data)
    assert result["skip"] == ["py<39"]

    # Test maximum Python version only
    toml_data = {"project": {"requires-python": "<3.12"}}
    result = build_build_section(toml_data)
    assert result["skip"] == ["py>=312"]

    # Test both minimum and maximum
    toml_data = {"project": {"requires-python": ">=3.9,<3.12"}}
    result = build_build_section(toml_data)
    assert result["skip"] == ["py<39", "py>=312"]


def test_build_build_section_no_skip_override():
    """Test that explicit skip configuration is not overridden."""
    toml_data = {
        "project": {"requires-python": ">=3.9"},
        "tool": {"conda": {"recipe": {"build": {"skip": ["win"]}}}},
    }
    result = build_build_section(toml_data)
    assert result["skip"] == ["win"]  # Should not add py<39


def test_detect_build_script():
    """Test _detect_build_script helper function."""
    from pyrattler_recipe_autogen.core import _detect_build_script

    # Test poetry
    build_system = {"build-backend": "poetry.core.masonry.api"}
    assert (
        _detect_build_script(build_system)
        == "poetry build && $PYTHON -m pip install dist/*.whl -vv"
    )

    # Test flit
    build_system = {"build-backend": "flit_core.buildapi"}
    assert _detect_build_script(build_system) == "$PYTHON -m flit install"

    # Test hatchling
    build_system = {"build-backend": "hatchling.build"}
    assert (
        _detect_build_script(build_system)
        == "$PYTHON -m pip install . -vv --no-build-isolation"
    )

    # Test default
    build_system = {"build-backend": "setuptools.build_meta"}
    assert (
        _detect_build_script(build_system)
        == "$PYTHON -m pip install . -vv --no-build-isolation"
    )


def test_detect_entry_points():
    """Test _detect_entry_points helper function."""
    from pyrattler_recipe_autogen.core import _detect_entry_points

    # Test with scripts
    project = {
        "scripts": {"my-cli": "mypackage.cli:main", "my-tool": "mypackage.tool:run"}
    }
    result = _detect_entry_points(project)
    assert result == ["my-cli = mypackage.cli:main", "my-tool = mypackage.tool:run"]

    # Test without scripts
    project = {}
    result = _detect_entry_points(project)
    assert result == []


def test_detect_skip_conditions():
    """Test _detect_skip_conditions helper function."""
    from pyrattler_recipe_autogen.core import _detect_skip_conditions

    # Test minimum version only
    assert _detect_skip_conditions(">=3.9") == ["py<39"]

    # Test maximum version only
    assert _detect_skip_conditions("<3.12") == ["py>=312"]

    # Test both min and max
    assert _detect_skip_conditions(">=3.9,<3.12") == ["py<39", "py>=312"]

    # Test empty string
    assert _detect_skip_conditions("") == []

    # Test with spaces
    assert _detect_skip_conditions(">= 3.10 , < 3.13") == ["py<310", "py>=313"]


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


def test_build_requirements_section_conditional_deps():
    """Test building requirements section with conditional dependencies."""
    toml_data = {
        "project": {
            "dependencies": [
                "tomli; python_version < '3.11'",
                "requests>=2.0",
                "numpy; python_version >= '3.9'",
            ]
        }
    }
    context = {"python_min": "3.8"}

    result = build_requirements_section(toml_data, context)

    # Should have python spec first
    assert result["run"][0] == "python >=3.8"

    # Should have conditional dependency for tomli
    tomli_dep = None
    numpy_dep = None
    for dep in result["run"]:
        if isinstance(dep, dict) and dep.get("if") == "py<311":
            tomli_dep = dep
        elif isinstance(dep, dict) and dep.get("if") == "py>=39":
            numpy_dep = dep

    assert tomli_dep is not None
    assert tomli_dep["then"] == ["tomli"]
    assert numpy_dep is not None
    assert numpy_dep["then"] == ["numpy"]

    # Should have unconditional dependency for requests
    assert "requests>=2.0" in result["run"]


def test_build_requirements_section_optional_deps():
    """Test building requirements section with optional dependencies."""
    toml_data = {
        "project": {
            "dependencies": ["requests"],
            "optional-dependencies": {
                "dev": ["pytest", "black"],
                "docs": ["sphinx", "myst-parser"],
            },
        }
    }
    context = {"python_min": "3.8"}

    result = build_requirements_section(toml_data, context)

    # Optional dependencies should not be in main requirements
    assert "pytest" not in result["run"]
    assert "sphinx" not in result["run"]

    # But should be stored in context for potential use
    assert "optional_dependencies" in context
    assert "dev" in context["optional_dependencies"]
    assert "docs" in context["optional_dependencies"]
    assert "pytest" in context["optional_dependencies"]["dev"]
    assert "sphinx" in context["optional_dependencies"]["docs"]


def test_convert_python_version_marker():
    """Test _convert_python_version_marker helper function."""
    from pyrattler_recipe_autogen.core import _convert_python_version_marker

    # Test less than version
    result = _convert_python_version_marker("tomli", 'python_version < "3.11"')
    assert result == {"if": "py<311", "then": ["tomli"]}

    # Test greater than or equal version
    result = _convert_python_version_marker("numpy", 'python_version >= "3.9"')
    assert result == {"if": "py>=39", "then": ["numpy"]}

    # Test unsupported marker
    with patch("pyrattler_recipe_autogen.core._warn") as mock_warn:
        result = _convert_python_version_marker("package", "unsupported_marker")
        assert result == "package"
        mock_warn.assert_called_once()


def test_process_conditional_dependencies():
    """Test _process_conditional_dependencies helper function."""
    from pyrattler_recipe_autogen.core import _process_conditional_dependencies

    deps = [
        "requests>=2.0",
        "tomli; python_version < '3.11'",
        "numpy; python_version >= '3.9'",
    ]

    result = _process_conditional_dependencies(deps)

    # First dependency should be unchanged
    assert result[0] == "requests>=2.0"

    # Second should be converted to conditional
    assert result[1] == {"if": "py<311", "then": ["tomli"]}

    # Third should be converted to conditional
    assert result[2] == {"if": "py>=39", "then": ["numpy"]}


def test_process_optional_dependencies():
    """Test _process_optional_dependencies helper function."""
    from pyrattler_recipe_autogen.core import _process_optional_dependencies

    optional_deps = {
        "dev": ["pytest", "black; python_version >= '3.8'"],
        "docs": ["sphinx"],
    }
    context = {}

    result = _process_optional_dependencies(optional_deps, context)

    assert "dev" in result
    assert "docs" in result
    assert "pytest" in result["dev"]
    assert "sphinx" in result["docs"]
    # The conditional dependency should be converted
    assert {"if": "py>=38", "then": ["black"]} in result["dev"]


def test_dedupe_mixed_requirements():
    """Test _dedupe_mixed_requirements helper function."""
    from pyrattler_recipe_autogen.core import _dedupe_mixed_requirements

    mixed_reqs = [
        "python>=3.8",
        "requests",
        {"if": "py<311", "then": ["tomli"]},
        "requests",  # duplicate
        {"if": "py>=39", "then": ["numpy"]},
        "python>=3.8",  # duplicate
    ]

    result = _dedupe_mixed_requirements(mixed_reqs)

    # Should dedupe strings but keep all dicts
    string_items = [item for item in result if isinstance(item, str)]
    dict_items = [item for item in result if isinstance(item, dict)]

    assert len(string_items) == 2  # python>=3.8 and requests (deduped)
    assert len(dict_items) == 2  # both conditional deps kept
    assert "python>=3.8" in string_items
    assert "requests" in string_items


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


def test_build_test_section_auto_detect_basic():
    """Test auto-detection of basic test configuration."""
    toml_data = {"project": {"name": "my-package", "dependencies": ["pytest>=6.0"]}}

    result = build_test_section(toml_data)
    assert result is not None
    assert "python" in result
    assert "imports" in result["python"]
    assert "my_package" in result["python"]["imports"]
    assert "pytest" in result["python"]["imports"]
    assert "commands" in result["python"]
    assert "python -m pytest" in result["python"]["commands"]


def test_build_test_section_auto_detect_pytest_config():
    """Test auto-detection when pytest is configured."""
    toml_data = {
        "project": {"name": "testpkg"},
        "tool": {"pytest": {"ini_options": {"testpaths": "tests"}}},
    }

    result = build_test_section(toml_data)
    assert result is not None
    assert "python" in result
    assert "commands" in result["python"]
    assert "python -m pytest" in result["python"]["commands"]


def test_build_test_section_auto_detect_optional_deps():
    """Test auto-detection of test requirements from optional dependencies."""
    toml_data = {
        "project": {
            "name": "testpkg",
            "optional-dependencies": {
                "test": ["pytest>=6.0", "coverage>=5.0"],
                "dev": ["black", "isort"],
            },
        }
    }

    result = build_test_section(toml_data)
    assert result is not None
    assert "requires" in result
    assert "pytest>=6.0" in result["requires"]
    assert "coverage>=5.0" in result["requires"]
    assert "black" in result["requires"]
    assert "isort" in result["requires"]


def test_build_test_section_auto_detect_unittest():
    """Test auto-detection with unittest."""
    toml_data = {
        "project": {"name": "testpkg", "dependencies": ["unittest-xml-reporting"]}
    }

    result = build_test_section(toml_data)
    assert result is not None
    assert "python" in result
    assert "commands" in result["python"]
    assert "python -m unittest discover" in result["python"]["commands"]


def test_build_test_section_auto_detect_hatch_scripts():
    """Test auto-detection of hatch test scripts."""
    toml_data = {
        "project": {"name": "testpkg"},
        "tool": {
            "hatch": {
                "envs": {
                    "test": {
                        "scripts": {
                            "run": "pytest tests/",
                            "cov": "pytest --cov=src tests/",
                        }
                    }
                }
            }
        },
    }

    result = build_test_section(toml_data)
    assert result is not None
    assert "python" in result
    assert "commands" in result["python"]
    commands = result["python"]["commands"]
    assert "pytest tests/" in commands
    assert "pytest --cov=src tests/" in commands


def test_build_test_section_no_auto_detect_with_explicit():
    """Test that explicit configuration takes precedence over auto-detection."""
    toml_data = {
        "project": {"name": "testpkg", "dependencies": ["pytest>=6.0"]},
        "tool": {"conda": {"recipe": {"test": {"imports": ["explicit_import"]}}}},
    }

    result = build_test_section(toml_data)
    assert result is not None
    assert result["imports"] == ["explicit_import"]
    # Should not have auto-detected content
    assert "python" not in result or "commands" not in result.get("python", {})


def test_detect_test_imports():
    """Test detection of test imports."""
    from pyrattler_recipe_autogen.core import _detect_test_imports

    toml_data = {
        "project": {
            "name": "my-awesome-package",
            "dependencies": ["pytest", "numpy"],
            "optional-dependencies": {"test": ["unittest2"], "testing": ["nose2"]},
        }
    }

    imports = _detect_test_imports(toml_data)
    assert "my_awesome_package" in imports
    assert "pytest" in imports
    assert "unittest2" in imports
    assert "nose2" in imports
    # Should not include numpy (not a test package)
    assert "numpy" not in imports


def test_detect_test_commands_complex():
    """Test detection of test commands from various sources."""
    from pyrattler_recipe_autogen.core import _detect_test_commands

    toml_data = {
        "project": {
            "name": "testpkg",
            "dependencies": ["pytest>=6.0"],
            "scripts": {"test": "pytest --verbose", "lint": "flake8"},
        },
        "tool": {
            "pytest": {"ini_options": {"testpaths": "tests"}},
            "hatch": {
                "envs": {
                    "test": {
                        "scripts": {
                            "unit": "pytest tests/unit/",
                            "integration": "pytest tests/integration/",
                        }
                    }
                }
            },
        },
    }

    commands = _detect_test_commands(toml_data)
    assert "python -m pytest" in commands
    assert "python -m pytest --verbose" in commands
    assert "pytest tests/unit/" in commands
    assert "pytest tests/integration/" in commands


def test_detect_test_requirements_various_groups():
    """Test detection of test requirements from various optional dependency groups."""
    from pyrattler_recipe_autogen.core import _detect_test_requirements

    toml_data = {
        "project": {
            "name": "testpkg",
            "optional-dependencies": {
                "test": ["pytest>=6.0", "pytest-cov"],
                "testing": ["hypothesis"],
                "dev": ["black", "isort"],
                "docs": ["sphinx"],  # Should not be included
            },
        }
    }

    requires = _detect_test_requirements(toml_data)
    assert "pytest>=6.0" in requires
    assert "pytest-cov" in requires
    assert "hypothesis" in requires
    assert "black" in requires
    assert "isort" in requires
    # Should not include docs dependencies
    assert "sphinx" not in requires


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


@patch("pyrattler_recipe_autogen.core.write_recipe_with_config")
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


# Tests for Enhanced Context Variables (Enhancement 5)


def test_detect_enhanced_context_variables():
    """Test enhanced context variable detection."""
    import tempfile

    from pyrattler_recipe_autogen.core import _detect_enhanced_context_variables

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = pathlib.Path(temp_dir)

        # Create test project structure
        (project_root / "src").mkdir()
        (project_root / "tests").mkdir()
        (project_root / "README.md").touch()
        (project_root / "LICENSE").touch()

        toml_data = {
            "project": {
                "name": "test-package",
                "dependencies": ["numpy>=1.20", "requests>=2.25"],
                "optional-dependencies": {
                    "dev": ["pytest", "mypy"],
                    "docs": ["sphinx"],
                },
                "scripts": {"test-cli": "test_package.cli:main"},
            },
            "build-system": {
                "requires": ["hatchling", "numpy"],
                "build-backend": "hatchling.build",
            },
            "tool": {"pytest": {"testpaths": ["tests"]}, "mypy": {"strict": True}},
        }

        result = _detect_enhanced_context_variables(toml_data, project_root)

        # Check package info
        assert result["package_name"] == "test-package"
        assert result["normalized_name"] == "test_package"
        assert result["conda_name"] == "test-package"
        assert result["src_dir"] == "src"
        assert result["has_scripts"] is True
        assert result["script_count"] == 1

        # Check build system info
        assert result["build_backend"] == "hatchling.build"
        assert result["uses_hatchling"] is True
        assert result["build_requires_count"] == 2
        assert result["has_compiled_extensions"] is True  # Due to numpy

        # Check dependency patterns
        assert result["dependency_count"] == 2
        assert "data_science" in result["dependency_categories"]
        assert result["optional_dep_groups"] == ["dev", "docs"]
        assert result["has_dev_dependencies"] is True
        assert result["has_doc_dependencies"] is True

        # Check development info
        assert result["test_dir"] == "tests"

        # Check tool configuration
        assert "pytest" in result["configured_tools"]
        assert "mypy" in result["configured_tools"]
        assert result["tool_count"] == 2


def test_detect_package_info():
    """Test package information detection."""
    import tempfile

    from pyrattler_recipe_autogen.core import _detect_package_info

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = pathlib.Path(temp_dir)
        (project_root / "src").mkdir()

        project = {
            "name": "my-awesome-package",
            "scripts": {"my-cli": "my_package.cli:main"},
            "gui-scripts": {"my-gui": "my_package.gui:main"},
        }

        result = _detect_package_info(project, project_root)

        assert result["package_name"] == "my-awesome-package"
        assert result["normalized_name"] == "my_awesome_package"
        assert result["conda_name"] == "my-awesome-package"
        assert result["src_dir"] == "src"
        assert result["has_scripts"] is True
        assert result["has_gui_scripts"] is True
        assert result["script_count"] == 1


def test_detect_package_info_namespace():
    """Test namespace package detection."""
    from pyrattler_recipe_autogen.core import _detect_package_info

    project = {"name": "namespace.subpackage"}
    result = _detect_package_info(project, pathlib.Path("."))

    assert result["namespace_package"] is True
    assert result["namespace"] == "namespace"


def test_analyze_build_backend():
    """Test build backend analysis."""
    from pyrattler_recipe_autogen.core import _analyze_build_backend

    # Test setuptools
    build_system = {"build-backend": "setuptools.build_meta"}
    result = _analyze_build_backend(build_system)
    assert result["uses_setuptools"] is True

    # Test hatchling
    build_system = {"build-backend": "hatchling.build"}
    result = _analyze_build_backend(build_system)
    assert result["uses_hatchling"] is True

    # Test flit
    build_system = {"build-backend": "flit_core.buildapi"}
    result = _analyze_build_backend(build_system)
    assert result["uses_flit"] is True


def test_analyze_build_requirements():
    """Test build requirements analysis."""
    from pyrattler_recipe_autogen.core import _analyze_build_requirements

    build_system = {"requires": ["hatchling", "cython>=0.29", "numpy>=1.20"]}

    result = _analyze_build_requirements(build_system)
    assert result["build_requires_count"] == 3
    assert result["has_compiled_extensions"] is True


def test_categorize_dependencies():
    """Test dependency categorization."""
    from pyrattler_recipe_autogen.core import _categorize_dependencies

    dependencies = [
        "numpy>=1.20",
        "requests>=2.25",
        "scipy>=1.7",  # Pure data science, not UI
        "matplotlib>=3.0",
    ]

    result = _categorize_dependencies(dependencies)
    expected_categories = {"data_science", "web"}
    assert set(result["dependency_categories"]) == expected_categories


def test_extract_dependency_name():
    """Test dependency name extraction."""
    from pyrattler_recipe_autogen.core import _extract_dependency_name

    test_cases = [
        ("numpy>=1.20.0", "numpy"),
        ("requests==2.25.1", "requests"),
        ("scipy~=1.7.0", "scipy"),
        ("matplotlib<4.0", "matplotlib"),
        ("pandas>1.0 ; python_version >= '3.8'", "pandas"),
    ]

    for dep_string, expected in test_cases:
        result = _extract_dependency_name(dep_string)
        assert result == expected


def test_analyze_optional_dependencies():
    """Test optional dependencies analysis."""
    from pyrattler_recipe_autogen.core import _analyze_optional_dependencies

    optional_deps = {
        "dev": ["pytest", "mypy", "ruff"],
        "test": ["pytest-cov", "pytest-xdist"],
        "docs": ["sphinx", "sphinx-rtd-theme"],
        "extra": ["optional-feature"],
    }

    result = _analyze_optional_dependencies(optional_deps)

    assert set(result["optional_dep_groups"]) == {"dev", "test", "docs", "extra"}
    assert result["optional_dep_count"] == 8
    assert result["has_dev_dependencies"] is True
    assert result["has_test_dependencies"] is True
    assert result["has_doc_dependencies"] is True


def test_detect_development_info():
    """Test development information detection."""
    import tempfile

    from pyrattler_recipe_autogen.core import _detect_development_info

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = pathlib.Path(temp_dir)

        # Create test structure
        tests_dir = project_root / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").touch()
        (tests_dir / "test_utils.py").touch()
        (project_root / "pytest.ini").touch()
        (project_root / ".pre-commit-config.yaml").touch()

        github_dir = project_root / ".github" / "workflows"
        github_dir.mkdir(parents=True)
        (github_dir / "ci.yml").touch()

        result = _detect_development_info({}, project_root)

        assert result["test_dir"] == "tests"
        assert result["test_file_count"] == 2
        assert "pytest" in result["config_files"]
        assert "pre_commit" in result["config_files"]
        assert result["has_ci_cd"] is True


def test_detect_license_info():
    """Test license information detection."""
    import tempfile

    from pyrattler_recipe_autogen.core import _detect_license_info

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = pathlib.Path(temp_dir)

        # Test license text
        project = {"license": {"text": "MIT License"}}
        result = _detect_license_info(project, project_root)
        assert result["license_type"] == "MIT"

        # Test license file
        license_file = project_root / "LICENSE"
        license_file.touch()
        project = {"license": {"file": "LICENSE"}}
        result = _detect_license_info(project, project_root)
        assert result["license_file"] == "LICENSE"

        # Test license string
        project = {"license": "Apache-2.0"}
        result = _detect_license_info(project, project_root)
        assert result["license_type"] == "Apache"


def test_classify_license():
    """Test license classification."""
    from pyrattler_recipe_autogen.core import _classify_license

    test_cases = [
        ("MIT License", "MIT"),
        ("Apache License 2.0", "Apache"),
        ("BSD 3-Clause License", "BSD"),
        ("GNU General Public License v3.0", "GPL"),
        ("GNU Lesser General Public License v2.1", "LGPL"),
        ("Mozilla Public License 2.0", "MPL"),
        ("Custom License", "Other"),
    ]

    for license_text, expected in test_cases:
        result = _classify_license(license_text)
        assert result == expected


def test_detect_documentation_info():
    """Test documentation detection."""
    import tempfile

    from pyrattler_recipe_autogen.core import _detect_documentation_info

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = pathlib.Path(temp_dir)

        # Test README detection only
        (project_root / "README.md").touch()
        result = _detect_documentation_info({}, project_root)
        assert result["readme_file"] == "README.md"

        # Test docs directory detection (create separate test without README)

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = pathlib.Path(temp_dir)

        # Test docs directory without README
        docs_dir = project_root / "docs"
        docs_dir.mkdir()
        (docs_dir / "conf.py").touch()  # Sphinx config

        result = _detect_documentation_info({}, project_root)
        assert result["has_docs_dir"] is True
        assert result["docs_generator"] == "sphinx"


def test_detect_repository_info():
    """Test repository information detection."""
    from pyrattler_recipe_autogen.core import _detect_repository_info

    # Test GitHub
    project = {"urls": {"repository": "https://github.com/user/repo"}}
    result = _detect_repository_info(project)
    assert result["hosted_on"] == "github"

    # Test GitLab
    project = {"urls": {"Repository": "https://gitlab.com/user/repo"}}
    result = _detect_repository_info(project)
    assert result["hosted_on"] == "gitlab"

    # Test Bitbucket
    project = {"urls": {"repository": "https://bitbucket.org/user/repo"}}
    result = _detect_repository_info(project)
    assert result["hosted_on"] == "bitbucket"


def test_build_context_section_enhanced():
    """Test context section with enhanced variables."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = pathlib.Path(temp_dir)
        (project_root / "src").mkdir()
        (project_root / "tests").mkdir()

        toml_data = {
            "project": {
                "name": "enhanced-test",
                "version": "1.0.0",
                "dependencies": ["numpy>=1.20"],
                "optional-dependencies": {"dev": ["pytest"]},
                "requires-python": ">=3.8,<3.12",
            },
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
            "tool": {"pytest": {}},
        }

        result = build_context_section(toml_data, project_root)

        # Standard context variables
        assert result["name"] == "enhanced-test"
        assert result["version"] == "1.0.0"
        assert result["python_min"] == "3.8"
        assert result["python_max"] == "3.12"

        # Enhanced context variables
        assert result["package_name"] == "enhanced-test"
        assert result["build_backend"] == "hatchling.build"
        assert result["dependency_count"] == 1
        assert result["has_dev_dependencies"] is True
        assert "pytest" in result["configured_tools"]


# Tests for Output Customization (Enhancement 6)


def test_output_config_initialization():
    """Test OutputConfig initialization with default values."""
    from pyrattler_recipe_autogen.core import OutputConfig

    config = OutputConfig()

    assert config.output_format == "yaml"
    assert config.yaml_style == "default"
    assert config.include_comments is True
    assert config.sort_keys is False
    assert config.indent == 2
    assert config.validate_output is True
    assert config.include_sections == []
    assert config.exclude_sections == []
    assert config.custom_templates == {}
    assert config.json_indent == 2


def test_output_config_custom_values():
    """Test OutputConfig with custom values."""
    from pyrattler_recipe_autogen.core import OutputConfig

    config = OutputConfig(
        output_format="json",
        yaml_style="block",
        include_comments=False,
        sort_keys=True,
        indent=4,
        validate_output=False,
        include_sections=["package", "build"],
        exclude_sections=["test"],
        custom_templates={"package": "custom template"},
        json_indent=4,
    )

    assert config.output_format == "json"
    assert config.yaml_style == "block"
    assert config.include_comments is False
    assert config.sort_keys is True
    assert config.indent == 4
    assert config.validate_output is False
    assert config.include_sections == ["package", "build"]
    assert config.exclude_sections == ["test"]
    assert config.custom_templates == {"package": "custom template"}
    assert config.json_indent == 4


def test_apply_output_customizations():
    """Test applying output customizations to recipe dictionary."""
    from pyrattler_recipe_autogen.core import OutputConfig, _apply_output_customizations

    recipe_dict = {
        "package": {"name": "test", "version": "1.0"},
        "build": {"script": "pip install ."},
        "requirements": {"run": ["python"]},
        "test": {"commands": ["pytest"]},
    }

    # Test section inclusion
    config = OutputConfig(include_sections=["package", "build"])
    result = _apply_output_customizations(recipe_dict, config)

    assert "package" in result
    assert "build" in result
    assert "requirements" not in result
    assert "test" not in result


def test_apply_output_customizations_exclusion():
    """Test section exclusion in output customizations."""
    from pyrattler_recipe_autogen.core import OutputConfig, _apply_output_customizations

    recipe_dict = {
        "package": {"name": "test", "version": "1.0"},
        "build": {"script": "pip install ."},
        "requirements": {"run": ["python"]},
        "test": {"commands": ["pytest"]},
    }

    # Test section exclusion
    config = OutputConfig(exclude_sections=["test"])
    result = _apply_output_customizations(recipe_dict, config)

    assert "package" in result
    assert "build" in result
    assert "requirements" in result
    assert "test" not in result


def test_validate_recipe_output():
    """Test recipe output validation."""
    import io
    import sys

    from pyrattler_recipe_autogen.core import OutputConfig, _validate_recipe_output

    # Capture stdout to check warning messages
    captured_output = io.StringIO()
    sys.stdout = captured_output

    # Test with missing required sections
    recipe_dict = {
        "package": {"name": "test"}  # Missing version
    }

    config = OutputConfig()
    _validate_recipe_output(recipe_dict, config)

    # Restore stdout
    sys.stdout = sys.__stdout__
    output = captured_output.getvalue()

    assert "Missing recommended sections" in output
    assert "Package version is missing" in output


def test_find_template_references():
    """Test finding template variable references."""
    from pyrattler_recipe_autogen.core import _find_template_references

    recipe_dict = {
        "package": {"name": "${{ name }}", "version": "${{ version }}"},
        "build": {"script": "pip install . --prefix=${{ prefix }}"},
        "requirements": {"run": ["python >=${{ python_min }}"]},
    }

    refs = _find_template_references(recipe_dict)
    expected_refs = {"name", "version", "prefix", "python_min"}

    assert refs == expected_refs


def test_validate_context_variables():
    """Test context variable validation."""
    import io
    import sys

    from pyrattler_recipe_autogen.core import _validate_context_variables

    # Capture stdout to check messages
    captured_output = io.StringIO()
    sys.stdout = captured_output

    recipe_dict = {
        "context": {"name": "test-package", "version": "1.0.0", "unused_var": "unused"},
        "package": {"name": "${{ name }}", "version": "${{ version }}"},
        "build": {"script": "echo ${{ undefined_var }}"},
    }

    _validate_context_variables(recipe_dict)

    # Restore stdout
    sys.stdout = sys.__stdout__
    output = captured_output.getvalue()

    assert "Undefined context variables: undefined_var" in output
    assert "Unused context variables: unused_var" in output


def test_write_yaml_output():
    """Test YAML output writing with configuration."""
    import tempfile

    from pyrattler_recipe_autogen.core import OutputConfig, _write_yaml_output

    recipe_dict = {
        "package": {"name": "test", "version": "1.0"},
        "build": {"script": "pip install ."},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp_path = pathlib.Path(tmp.name)

    try:
        config = OutputConfig(sort_keys=True, indent=4)
        _write_yaml_output(recipe_dict, tmp_path, config)

        # Verify file was written
        assert tmp_path.exists()

        # Verify content
        with tmp_path.open("r") as f:
            content = f.read()
            assert "name: test" in content
            assert "version: '1.0'" in content or "version: 1.0" in content
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_write_json_output():
    """Test JSON output writing with configuration."""
    import json
    import tempfile

    from pyrattler_recipe_autogen.core import OutputConfig, _write_json_output

    recipe_dict = {
        "package": {"name": "test", "version": "1.0"},
        "build": {"script": "pip install ."},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp_path = pathlib.Path(tmp.name)

    try:
        config = OutputConfig(json_indent=4, sort_keys=True)
        _write_json_output(recipe_dict, tmp_path, config)

        # Should change extension to .json
        json_path = tmp_path.with_suffix(".json")
        assert json_path.exists()

        # Verify content
        with json_path.open("r") as f:
            loaded_data = json.load(f)
            assert loaded_data["package"]["name"] == "test"
            assert loaded_data["package"]["version"] == "1.0"

        # Cleanup json file too
        json_path.unlink()
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_load_output_config():
    """Test loading output configuration from pyproject.toml."""
    from pyrattler_recipe_autogen.core import _load_output_config

    # Test with custom output configuration
    toml_data = {
        "tool": {
            "conda": {
                "recipe": {
                    "output": {
                        "format": "json",
                        "yaml_style": "block",
                        "include_comments": False,
                        "sort_keys": True,
                        "indent": 4,
                        "validate_output": False,
                        "include_sections": ["package", "build"],
                        "exclude_sections": ["test"],
                        "json_indent": 4,
                    }
                }
            }
        }
    }

    config = _load_output_config(toml_data)

    assert config.output_format == "json"
    assert config.yaml_style == "block"
    assert config.include_comments is False
    assert config.sort_keys is True
    assert config.indent == 4
    assert config.validate_output is False
    assert config.include_sections == ["package", "build"]
    assert config.exclude_sections == ["test"]
    assert config.json_indent == 4


def test_load_output_config_defaults():
    """Test loading output configuration with defaults."""
    from pyrattler_recipe_autogen.core import _load_output_config

    # Test with no output configuration
    toml_data = {}

    config = _load_output_config(toml_data)

    assert config.output_format == "yaml"
    assert config.yaml_style == "default"
    assert config.include_comments is True
    assert config.sort_keys is False
    assert config.indent == 2
    assert config.validate_output is True


def test_generate_recipe_with_config():
    """Test recipe generation with custom configuration."""
    import tempfile

    from pyrattler_recipe_autogen.core import OutputConfig, generate_recipe_with_config

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)

        # Create a test pyproject.toml
        pyproject_path = temp_path / "pyproject.toml"
        pyproject_content = """
[project]
name = "test-package"
version = "1.0.0"
dependencies = ["requests"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
        pyproject_path.write_text(pyproject_content)

        # Test with JSON output configuration
        output_path = temp_path / "recipe.yaml"
        config = OutputConfig(
            output_format="json", sort_keys=True, exclude_sections=["test"]
        )

        generate_recipe_with_config(pyproject_path, output_path, config)

        # Should create JSON file
        json_path = output_path.with_suffix(".json")
        assert json_path.exists()

        # Verify content
        import json

        with json_path.open("r") as f:
            recipe_data = json.load(f)
            assert recipe_data["package"]["name"] == "${{ name }}"
            assert "test" not in recipe_data  # Should be excluded


# Tests for Integration Enhancements (Enhancement 7)


def test_integration_config_initialization():
    """Test IntegrationConfig initialization with default values."""
    from pyrattler_recipe_autogen.core import IntegrationConfig

    config = IntegrationConfig()

    assert config.pixi_integration is True
    assert config.ci_cd_detection is True
    assert config.precommit_integration is True
    assert config.dev_workflow_optimization is True
    assert config.suggest_improvements is True


def test_integration_config_custom_values():
    """Test IntegrationConfig with custom values."""
    from pyrattler_recipe_autogen.core import IntegrationConfig

    config = IntegrationConfig(
        pixi_integration=False,
        ci_cd_detection=False,
        precommit_integration=True,
        dev_workflow_optimization=True,
        suggest_improvements=False,
    )

    assert config.pixi_integration is False
    assert config.ci_cd_detection is False
    assert config.precommit_integration is True
    assert config.dev_workflow_optimization is True
    assert config.suggest_improvements is False


def test_detect_pixi_integration():
    """Test pixi integration detection."""
    import tempfile

    from pyrattler_recipe_autogen.core import _detect_pixi_integration

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)

        # Test with no pixi files
        result = _detect_pixi_integration(temp_path)
        assert result["detected"] is False

        # Test with pixi.lock only
        (temp_path / "pixi.lock").touch()
        result = _detect_pixi_integration(temp_path)
        assert result["detected"] is True
        assert result["has_pixi_lock"] is True
        assert result["has_pixi_toml"] is False

        # Test with pixi.toml
        pixi_toml_content = """
[project]
name = "test"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-64"]

[tasks]
test = "pytest"

[environments]
dev = ["test"]
"""
        (temp_path / "pixi.toml").write_text(pixi_toml_content)
        result = _detect_pixi_integration(temp_path)
        assert result["detected"] is True
        assert result["has_pixi_toml"] is True
        assert result["channels"] == ["conda-forge"]
        assert result["platforms"] == ["linux-64", "osx-64"]
        assert result["environments"] == ["dev"]
        assert "test" in result["tasks"]


def test_detect_ci_cd_systems():
    """Test CI/CD system detection."""
    import tempfile

    from pyrattler_recipe_autogen.core import _detect_ci_cd_systems

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)

        # Test with no CI/CD
        result = _detect_ci_cd_systems(temp_path)
        assert result == []

        # Test GitHub Actions
        github_dir = temp_path / ".github" / "workflows"
        github_dir.mkdir(parents=True)
        (github_dir / "ci.yml").touch()
        result = _detect_ci_cd_systems(temp_path)
        assert "github-actions" in result

        # Test GitLab CI
        (temp_path / ".gitlab-ci.yml").touch()
        result = _detect_ci_cd_systems(temp_path)
        assert "gitlab-ci" in result

        # Test Travis CI
        (temp_path / ".travis.yml").touch()
        result = _detect_ci_cd_systems(temp_path)
        assert "travis-ci" in result


def test_detect_precommit_config():
    """Test pre-commit configuration detection."""
    import tempfile

    from pyrattler_recipe_autogen.core import _detect_precommit_config

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)

        # Test with no pre-commit config
        result = _detect_precommit_config(temp_path)
        assert result is None

        # Test with valid pre-commit config
        precommit_content = """
repos:
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.4.0
  hooks:
  - id: trailing-whitespace
"""
        (temp_path / ".pre-commit-config.yaml").write_text(precommit_content)
        result = _detect_precommit_config(temp_path)
        assert result is not None
        assert "repos" in result


def test_detect_dev_tools():
    """Test development tool detection."""
    import tempfile

    from pyrattler_recipe_autogen.core import _detect_dev_tools

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)

        # Test with pyproject.toml tool configurations
        toml_data = {
            "tool": {
                "pytest": {"testpaths": ["tests"]},
                "mypy": {"strict": True},
                "ruff": {"line-length": 88},
            }
        }

        result = _detect_dev_tools(temp_path, toml_data)
        assert "pytest" in result
        assert "mypy" in result
        assert "ruff" in result

        # Test with config files
        (temp_path / "tox.ini").touch()
        (temp_path / ".coveragerc").touch()

        result = _detect_dev_tools(temp_path, {})
        assert "tox" in result
        assert "coverage" in result


def test_generate_workflow_suggestions():
    """Test workflow suggestion generation."""
    from pyrattler_recipe_autogen.core import (
        IntegrationInfo,
        _generate_workflow_suggestions,
    )

    # Test with minimal setup
    integration_info = IntegrationInfo()
    suggestions = _generate_workflow_suggestions(integration_info)

    assert any("pixi" in s for s in suggestions)
    assert any("CI/CD" in s or "GitHub Actions" in s for s in suggestions)
    assert any("pre-commit" in s for s in suggestions)

    # Test with some tools detected
    integration_info.pixi_detected = True
    integration_info.dev_tools = ["pytest"]
    suggestions = _generate_workflow_suggestions(integration_info)

    # Should suggest missing essential tools
    assert any("mypy" in s and "ruff" in s for s in suggestions)


def test_generate_integration_recommendations():
    """Test integration recommendation generation."""
    from pyrattler_recipe_autogen.core import (
        IntegrationInfo,
        _generate_integration_recommendations,
    )

    # Test with GPU dependencies
    toml_data = {
        "project": {"dependencies": ["tensorflow-gpu", "numpy"]},
        "build-system": {"build-backend": "setuptools.build_meta"},
    }

    integration_info = IntegrationInfo(pixi_detected=True)
    recommendations = _generate_integration_recommendations(integration_info, toml_data)

    assert any("conda-forge alternatives" in r for r in recommendations)
    assert any("hatchling" in r for r in recommendations)


def test_detect_integration_enhancements():
    """Test comprehensive integration detection."""
    import tempfile

    from pyrattler_recipe_autogen.core import (
        IntegrationConfig,
        _detect_integration_enhancements,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)

        # Create test environment
        (temp_path / "pixi.toml").write_text("[project]\nname = 'test'")
        (temp_path / ".pre-commit-config.yaml").write_text("repos: []")

        github_dir = temp_path / ".github" / "workflows"
        github_dir.mkdir(parents=True)
        (github_dir / "ci.yml").touch()

        toml_data = {"tool": {"pytest": {}, "mypy": {}}}

        config = IntegrationConfig()
        result = _detect_integration_enhancements(temp_path, toml_data, config)

        assert result.pixi_detected is True
        assert result.precommit_detected is True
        assert "github-actions" in result.ci_cd_systems
        assert "pytest" in result.dev_tools
        assert "mypy" in result.dev_tools
        assert len(result.workflow_suggestions) > 0


def test_load_integration_config():
    """Test loading integration configuration from pyproject.toml."""
    from pyrattler_recipe_autogen.core import _load_integration_config

    # Test with custom configuration
    toml_data = {
        "tool": {
            "conda": {
                "recipe": {
                    "integration": {
                        "pixi_integration": False,
                        "ci_cd_detection": True,
                        "suggest_improvements": False,
                    }
                }
            }
        }
    }

    config = _load_integration_config(toml_data)

    assert config.pixi_integration is False
    assert config.ci_cd_detection is True
    assert config.suggest_improvements is False
    assert config.precommit_integration is True  # Default value


def test_load_integration_config_defaults():
    """Test loading integration configuration with defaults."""
    from pyrattler_recipe_autogen.core import _load_integration_config

    # Test with no configuration
    toml_data = {}

    config = _load_integration_config(toml_data)

    assert config.pixi_integration is True
    assert config.ci_cd_detection is True
    assert config.precommit_integration is True
    assert config.dev_workflow_optimization is True
    assert config.suggest_improvements is True


if __name__ == "__main__":
    pytest.main([__file__])
