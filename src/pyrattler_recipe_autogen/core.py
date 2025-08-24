"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

import tomli

logger = logging.getLogger(__name__)

# ----
# Core business logic for generating Rattler-Build recipe.yaml from pyproject.toml
#
# • Pulls canonical project data from `[project]`
# • Handles dynamic version resolution from build backends
# • If `[tool.pixi]` exists, uses Pixi tables for requirement mapping
# • Reads extra/override keys from `[tool.conda.recipe.*]`
# ----

# Optional setuptools_scm import handled within function
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import typing as _t
from typing import Union

try:
    import tomllib  # Python ≥3.11
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

# Note: setuptools_scm import handled locally in resolve_dynamic_version()

import yaml

# ----
# Utilities
# ----


def _toml_get(d: dict, dotted_key: str, default: _t.Any = None) -> _t.Any:
    """Nested lookup with `.` notation."""
    cur = d
    for part in dotted_key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def _merge_dict(base: dict, extra: dict | None) -> dict:
    """Return `extra` merged *into* `base` (shallow)."""
    if extra:
        merged = base.copy()
        merged.update(extra)
        return merged
    return base


def _get_relative_path(
    file_path: str | pathlib.Path, recipe_dir: str | pathlib.Path
) -> str:
    """
    Get relative path from recipe_dir to file_path, using '../' as needed.

    Args:
        file_path: Path to the file
        recipe_dir: Path to the recipe directory

    Returns:
        Relative path string from recipe_dir to file_path
    """
    file_path = pathlib.Path(file_path).resolve()
    recipe_dir = pathlib.Path(recipe_dir).resolve()

    try:
        # Try direct relative_to first (for files within recipe_dir)
        return str(file_path.relative_to(recipe_dir))
    except ValueError:
        # File is not within recipe_dir, compute path using common ancestor
        try:
            # Find common path and build relative path with ../
            # Note: os.path.commonpath can raise ValueError on Windows when paths are on different drives
            common = pathlib.Path(os.path.commonpath([file_path, recipe_dir]))

            # Get path from recipe_dir back to common ancestor
            recipe_to_common = recipe_dir.relative_to(common)

            # Get path from common ancestor to file
            common_to_file = file_path.relative_to(common)

            # Build relative path: go up from recipe_dir to common, then down to file
            up_dirs = [".."] * len(recipe_to_common.parts)
            relative_path = pathlib.Path(*up_dirs) / common_to_file

            return str(relative_path)
        except ValueError:
            # Handle Windows cross-drive path issues or other path resolution failures
            return str(file_path)
        except OSError:
            # Handle filesystem-related errors
            return str(file_path)


def _warn(msg: str) -> None:
    print(f"⚠ {msg}", file=sys.stderr)


def _normalize_deps(deps: _t.Any) -> list[str]:
    """Convert dependencies from dict or list format to list of strings."""
    if isinstance(deps, dict):
        # Convert {"numpy": ">=1.0", "scipy": "*"} to ["numpy>=1.0", "scipy"]
        result = []
        for name, spec in deps.items():
            if spec == "*" or spec == "":
                result.append(name)
            else:
                result.append(f"{name}{spec}")
        return result
    elif isinstance(deps, list):
        return deps
    else:
        return []


# ----
# Version Resolution
# ----


def resolve_dynamic_version(project_root: pathlib.Path, toml: dict) -> str:
    """
    Attempt to resolve dynamic version from the build backend.
    Returns a version string or raises an exception.
    """
    build_system = toml.get("build-system", {})
    build_backend = build_system.get("build-backend", "")

    # Try setuptools_scm first (most common)
    if (
        "setuptools_scm" in build_backend
        or "tool" in toml
        and "setuptools_scm" in toml["tool"]
    ):
        # Try to import setuptools_scm locally
        _setuptools_scm = None
        try:
            import setuptools_scm  # noqa: F401 # local import

            _setuptools_scm = setuptools_scm
        except ImportError:
            pass

        if _setuptools_scm is not None:
            try:
                return str(_setuptools_scm.get_version(root=project_root))
            except (OSError, ValueError, RuntimeError, ImportError) as e:
                # Fall through to subprocess approach if setuptools_scm fails
                _warn(f"setuptools_scm direct call failed: {e}")
            except Exception as e:
                # Catch any other unexpected exceptions and log them
                _warn(f"Unexpected error with setuptools_scm: {e}")

        # Try setuptools_scm via subprocess if direct import failed or not available
        _warn("setuptools_scm not available, trying command line")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "setuptools_scm"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    # Try hatchling
    if "hatchling" in build_backend or "hatch" in build_backend:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "hatch", "version"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    # Try poetry
    if "poetry" in build_backend:
        try:
            result = subprocess.run(
                ["poetry", "version", "-s"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    # Last resort: use environment variable placeholder
    _warn("Could not resolve dynamic version, using environment variable placeholder")
    return "${{ env.get('PYPROJECT_VERSION', default='0.1.0') }}"


# ----
# Section Builders
# ----


def build_context_section(toml: dict, project_root: pathlib.Path) -> dict:
    """Build the context section of the recipe with enhanced auto-detection."""
    project = toml["project"]

    # Handle dynamic version
    dynamic_fields = project.get("dynamic", [])
    if "version" in dynamic_fields:
        if "version" in project:
            _warn("Version is marked as dynamic but also present in project table")
        version = resolve_dynamic_version(project_root, toml)
    else:
        version = project.get("version")
        if not version:
            raise ValueError(
                "Version not found in project table and not marked as dynamic"
            )

    # Extract python_min and python_max from requires-python
    requires_python = project.get("requires-python", "")
    python_min = ""
    python_max = ""
    if requires_python:
        # Remove common range modifiers to get the base version
        # Handle cases like ">=3.12", "~=3.12.0", ">=3.12,<4.0", ">=3.8,<3.13", etc.
        # Extract the first version number after >= or ~=
        min_match = re.search(r"[>~]=?\s*([0-9]+(?:\.[0-9]+)*)", requires_python)
        if min_match:
            python_min = min_match.group(1)

        # Extract the maximum version number after <
        max_match = re.search(r"<\s*([0-9]+(?:\.[0-9]+)*)", requires_python)
        if max_match:
            python_max = max_match.group(1)

    # Start with standard context
    context = {
        "name": project["name"].lower().replace(" ", "-"),
        "version": version,
        "python_min": python_min,
    }

    # Only add python_max if it has a valid value
    if python_max:
        context["python_max"] = python_max

    # Add enhanced context variables
    enhanced_context = _detect_enhanced_context_variables(toml, project_root)
    context.update(enhanced_context)

    # Add platform/variant context variables
    platform_context = _detect_platform_variants(toml)
    context.update(platform_context)

    # Store optional dependencies for potential variant use
    optional_deps = project.get("optional-dependencies", {})
    if optional_deps:
        context["optional_dependencies"] = optional_deps

    # Merge in extra context from tool.conda.recipe.extra_context
    # This will override any auto-detected values if explicitly provided
    extra_context = _toml_get(toml, "tool.conda.recipe.extra_context", {})
    context.update(extra_context)

    return context


def _detect_enhanced_context_variables(
    toml: dict, project_root: pathlib.Path
) -> dict[str, _t.Any]:
    """Detect enhanced context variables for advanced recipe generation."""
    project = toml.get("project", {})
    context = {}

    # Detect common naming conventions and patterns
    package_info = _detect_package_info(project, project_root)
    context.update(package_info)

    # Detect build system and tool configurations
    build_info = _detect_build_system_info(toml)
    context.update(build_info)

    # Detect dependency patterns and constraints
    dep_info = _detect_dependency_patterns(project)
    context.update(dep_info)

    # Detect development and testing configurations
    dev_info = _detect_development_info(toml, project_root)
    context.update(dev_info)

    # Detect license and documentation patterns
    meta_info = _detect_metadata_patterns(project, project_root)
    context.update(meta_info)

    return context


def _detect_package_info(
    project: dict[str, _t.Any], project_root: pathlib.Path
) -> dict[str, _t.Any]:
    """Detect package naming and structure information."""
    info: dict[str, _t.Any] = {}

    # Package naming variations
    name = project.get("name", "")
    if name:
        info["package_name"] = name
        info["normalized_name"] = name.lower().replace("-", "_").replace(" ", "_")
        info["conda_name"] = name.lower().replace("_", "-").replace(" ", "-")

        # Detect if it's a namespace package
        if "." in name:
            info["namespace_package"] = True
            info["namespace"] = name.split(".")[0]

    # Source directory detection
    src_patterns = ["src", "lib", project.get("name", "").replace("-", "_")]
    for pattern in src_patterns:
        src_path = project_root / pattern
        if src_path.exists() and src_path.is_dir():
            info["src_dir"] = pattern
            break

    # Entry points detection
    entry_points = project.get("scripts", {})
    if entry_points:
        info["has_scripts"] = True
        info["script_count"] = len(entry_points)

    gui_scripts = project.get("gui-scripts", {})
    if gui_scripts:
        info["has_gui_scripts"] = True

    return info


def _detect_build_system_info(toml: dict[str, _t.Any]) -> dict[str, _t.Any]:
    """Detect build system and tool configuration information."""
    info: dict[str, _t.Any] = {}

    # Build system detection
    build_system = toml.get("build-system", {})
    if build_system:
        info.update(_analyze_build_backend(build_system))
        info.update(_analyze_build_requirements(build_system))

    # Tool configurations
    tool_config = toml.get("tool", {})
    if tool_config:
        info.update(_analyze_tool_config(tool_config))

    return info


def _analyze_build_backend(build_system: dict[str, _t.Any]) -> dict[str, _t.Any]:
    """Analyze build backend information."""
    info: dict[str, _t.Any] = {}
    build_backend = build_system.get("build-backend", "")
    info["build_backend"] = build_backend

    # Common build backend patterns
    backend_map = {
        "setuptools": "uses_setuptools",
        "flit": "uses_flit",
        "poetry": "uses_poetry",
        "hatch": "uses_hatchling",
    }

    for backend_name, info_key in backend_map.items():
        if backend_name in build_backend:
            info[info_key] = True
            break

    return info


def _analyze_build_requirements(build_system: dict[str, _t.Any]) -> dict[str, _t.Any]:
    """Analyze build requirements."""
    info: dict[str, _t.Any] = {}
    build_requires = build_system.get("requires", [])
    if build_requires:
        info["build_requires_count"] = len(build_requires)
        # Check for compiled extensions
        compiled_indicators = ["cython", "pybind", "numpy"]
        if any(
            indicator in req.lower()
            for req in build_requires
            for indicator in compiled_indicators
        ):
            info["has_compiled_extensions"] = True
    return info


def _analyze_tool_config(tool_config: dict[str, _t.Any]) -> dict[str, _t.Any]:
    """Analyze tool configurations."""
    info: dict[str, _t.Any] = {}
    tool_names = [
        "pytest",
        "mypy",
        "ruff",
        "black",
        "isort",
        "flake8",
        "bandit",
        "coverage",
    ]
    detected_tools = [tool for tool in tool_names if tool in tool_config]

    if detected_tools:
        info["configured_tools"] = detected_tools
        info["tool_count"] = len(detected_tools)

    return info


def _detect_dependency_patterns(project: dict[str, _t.Any]) -> dict[str, _t.Any]:
    """Detect dependency patterns and constraints."""
    info: dict[str, _t.Any] = {}

    # Main dependencies analysis
    dependencies = project.get("dependencies", [])
    if dependencies:
        info["dependency_count"] = len(dependencies)
        info.update(_categorize_dependencies(dependencies))

    # Optional dependencies analysis
    optional_deps = project.get("optional-dependencies", {})
    if optional_deps:
        info.update(_analyze_optional_dependencies(optional_deps))

    return info


def _categorize_dependencies(dependencies: list[str]) -> dict[str, _t.Any]:
    """Categorize dependencies by type."""
    info: dict[str, _t.Any] = {}
    ui_deps = [
        "tkinter",
        "qt",
        "gtk",
        "kivy",
        "streamlit",
        "gradio",
        "dash",
        "flask",
        "django",
        "fastapi",
    ]
    data_deps = [
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "seaborn",
        "plotly",
        "scikit-learn",
        "tensorflow",
        "pytorch",
        "torch",
    ]
    web_deps = ["requests", "httpx", "aiohttp", "urllib3", "beautifulsoup4", "selenium"]

    categories = []
    for dep in dependencies:
        dep_name = _extract_dependency_name(dep)
        if any(ui_dep in dep_name.lower() for ui_dep in ui_deps):
            categories.append("ui")
        elif any(data_dep in dep_name.lower() for data_dep in data_deps):
            categories.append("data_science")
        elif any(web_dep in dep_name.lower() for web_dep in web_deps):
            categories.append("web")

    if categories:
        info["dependency_categories"] = list(set(categories))
    return info


def _extract_dependency_name(dep: str) -> str:
    """Extract clean dependency name from requirement string."""
    separators = [">=", "==", "~=", "<", ">", " "]
    dep_name = dep
    for sep in separators:
        dep_name = dep_name.split(sep)[0]
    return dep_name


def _analyze_optional_dependencies(
    optional_deps: dict[str, list[str]],
) -> dict[str, _t.Any]:
    """Analyze optional dependency groups."""
    info: dict[str, _t.Any] = {}
    info["optional_dep_groups"] = list(optional_deps.keys())
    info["optional_dep_count"] = sum(len(deps) for deps in optional_deps.values())

    # Common patterns
    group_patterns = {
        "has_dev_dependencies": ["dev", "development"],
        "has_test_dependencies": ["test", "testing"],
        "has_doc_dependencies": ["docs", "documentation"],
    }

    for info_key, patterns in group_patterns.items():
        if any(pattern in optional_deps for pattern in patterns):
            info[info_key] = True

    return info


def _detect_development_info(
    _toml: dict[str, _t.Any], project_root: pathlib.Path
) -> dict[str, _t.Any]:
    """Detect development and testing configuration."""
    info: dict[str, _t.Any] = {}

    # Test directory detection
    test_dirs = ["tests", "test", "testing"]
    for test_dir in test_dirs:
        test_path = project_root / test_dir
        if test_path.exists() and test_path.is_dir():
            info["test_dir"] = test_dir
            # Count test files
            test_files = list(test_path.glob("test_*.py")) + list(
                test_path.glob("*_test.py")
            )
            if test_files:
                info["test_file_count"] = len(test_files)
            break

    # Configuration files detection
    config_files = {
        "tox.ini": "tox",
        "pytest.ini": "pytest",
        ".pre-commit-config.yaml": "pre_commit",
        "Makefile": "make",
        "justfile": "just",
        "noxfile.py": "nox",
    }

    detected_configs = []
    for config_file, tool_name in config_files.items():
        if (project_root / config_file).exists():
            detected_configs.append(tool_name)

    if detected_configs:
        info["config_files"] = detected_configs

    # CI/CD detection
    ci_dirs = [".github/workflows", ".gitlab-ci", ".circleci"]
    for ci_dir in ci_dirs:
        ci_path = project_root / ci_dir
        if ci_path.exists():
            info["has_ci_cd"] = True
            break

    return info


def _detect_metadata_patterns(
    project: dict[str, _t.Any], project_root: pathlib.Path
) -> dict[str, _t.Any]:
    """Detect license and documentation patterns."""
    info: dict[str, _t.Any] = {}

    # License detection
    info.update(_detect_license_info(project, project_root))

    # Documentation detection
    info.update(_detect_documentation_info(project, project_root))

    # Repository URLs
    info.update(_detect_repository_info(project))

    return info


def _detect_license_info(
    project: dict[str, _t.Any], project_root: pathlib.Path
) -> dict[str, _t.Any]:
    """Detect license information."""
    info: dict[str, _t.Any] = {}
    license_info = project.get("license")

    if not license_info:
        return info

    if isinstance(license_info, dict):
        license_text = license_info.get("text", "")
        license_file = license_info.get("file", "")
        if license_text:
            info["license_type"] = _classify_license(license_text)
        elif license_file:
            license_path = project_root / license_file
            if license_path.exists():
                info["license_file"] = license_file
    elif isinstance(license_info, str):
        info["license_type"] = _classify_license(license_info)

    return info


def _detect_documentation_info(
    _project: dict[str, _t.Any], project_root: pathlib.Path
) -> dict[str, _t.Any]:
    """Detect documentation configuration."""
    info: dict[str, _t.Any] = {}
    doc_files = ["README.md", "README.rst", "README.txt", "docs"]

    for doc_file in doc_files:
        doc_path = project_root / doc_file
        if doc_path.exists():
            if doc_file == "docs" and doc_path.is_dir():
                info["has_docs_dir"] = True
                info.update(_detect_docs_generator(doc_path, project_root))
            else:
                info["readme_file"] = doc_file
                break

    return info


def _detect_docs_generator(
    docs_path: pathlib.Path, project_root: pathlib.Path
) -> dict[str, _t.Any]:
    """Detect documentation generator type."""
    info: dict[str, _t.Any] = {}

    if (docs_path / "conf.py").exists():
        info["docs_generator"] = "sphinx"
    elif (docs_path / "mkdocs.yml").exists() or (project_root / "mkdocs.yml").exists():
        info["docs_generator"] = "mkdocs"

    return info


def _detect_repository_info(project: dict[str, _t.Any]) -> dict[str, _t.Any]:
    """Detect repository hosting information."""
    info: dict[str, _t.Any] = {}
    urls = project.get("urls", {})

    if not urls:
        return info

    repo_url = urls.get("repository") or urls.get("Repository")
    if repo_url:
        hosting_map = {
            "github.com": "github",
            "gitlab.com": "gitlab",
            "bitbucket.org": "bitbucket",
        }

        for domain, host_name in hosting_map.items():
            if domain in repo_url:
                info["hosted_on"] = host_name
                break

    return info


def _classify_license(license_text: str) -> str:
    """Classify license type from license text."""
    license_lower = license_text.lower()

    if "mit" in license_lower:
        return "MIT"
    elif "apache" in license_lower:
        return "Apache"
    elif "bsd" in license_lower:
        return "BSD"
    elif "lgpl" in license_lower or "lesser general public license" in license_lower:
        return "LGPL"
    elif "gpl" in license_lower or "general public license" in license_lower:
        return "GPL"
    elif "mozilla" in license_lower or "mpl" in license_lower:
        return "MPL"
    else:
        return "Other"


def _detect_platform_variants(toml: dict) -> dict[str, _t.Any]:
    """Detect platform-specific variants and configurations."""
    project = toml.get("project", {})
    variants: dict[str, _t.Any] = {}

    # Detect Python version variants
    python_variants = _detect_python_variants(project)
    if python_variants:
        variants["python_variants"] = python_variants

    # Detect platform-specific dependencies
    platform_deps = _detect_platform_dependencies(project)
    if platform_deps:
        variants["platform_dependencies"] = platform_deps

    # Detect architecture-specific configurations
    arch_config = _detect_architecture_config(toml)
    if arch_config:
        variants.update(arch_config)

    # Detect OS-specific configurations
    os_config = _detect_os_config(project)
    if os_config:
        variants.update(os_config)

    return variants


def _detect_python_variants(project: dict) -> list[str]:
    """Detect Python version variants from classifiers and requirements."""
    python_versions = set()

    # Extract from classifiers
    classifier_versions = _extract_versions_from_classifiers(
        project.get("classifiers", [])
    )
    python_versions.update(classifier_versions)

    # Extract from requires-python
    requires_versions = _extract_versions_from_requires(
        project.get("requires-python", "")
    )
    python_versions.update(requires_versions)

    # Sort versions numerically (not alphabetically)
    return sorted(python_versions, key=lambda v: tuple(map(int, v.split("."))))


def _extract_versions_from_classifiers(classifiers: list[str]) -> set[str]:
    """Extract Python versions from project classifiers."""
    versions = set()
    for classifier in classifiers:
        if "Programming Language :: Python ::" in classifier:
            # Extract version like "Programming Language :: Python :: 3.9"
            parts = classifier.split("::")
            if len(parts) >= 3:
                version_part = parts[-1].strip()
                # Match versions like "3.9", "3.10", "3.11"
                if re.match(r"^\d+\.\d+$", version_part):
                    versions.add(version_part)
    return versions


def _extract_versions_from_requires(requires_python: str) -> set[str]:
    """Extract Python versions from requires-python specification."""
    if not requires_python:
        return set()

    versions = set()

    # Parse version ranges like ">=3.8,<4.0" or ">=3.9"
    min_match = re.search(r">=\s*(\d+)\.(\d+)", requires_python)
    max_match = re.search(r"<\s*(\d+)\.(\d+)", requires_python)

    if min_match:
        min_major, min_minor = int(min_match.group(1)), int(min_match.group(2))
        max_major, max_minor = 4, 0  # Default upper bound

        if max_match:
            max_major, max_minor = int(max_match.group(1)), int(max_match.group(2))

        # Generate supported versions
        versions.update(
            _generate_version_range(min_major, min_minor, max_major, max_minor)
        )

    return versions


def _generate_version_range(
    min_major: int, min_minor: int, max_major: int, max_minor: int
) -> set[str]:
    """Generate Python version range between min and max versions."""
    versions = set()
    current_major, current_minor = min_major, min_minor

    while (current_major, current_minor) < (max_major, max_minor):
        versions.add(f"{current_major}.{current_minor}")
        current_minor += 1
        if current_minor > 12:  # Reasonable upper bound for minor versions
            current_major += 1
            current_minor = 0

    return versions


def _detect_platform_dependencies(project: dict) -> dict[str, list[str]]:
    """Detect platform-specific dependencies from environment markers."""
    platform_deps: dict[str, list[str]] = {}
    dependencies = project.get("dependencies", [])

    for dep in dependencies:
        if ";" in dep:
            platform_info = _parse_dependency_marker(dep)
            if platform_info:
                platform, dep_name = platform_info
                if platform not in platform_deps:
                    platform_deps[platform] = []
                platform_deps[platform].append(dep_name)

    return platform_deps


def _parse_dependency_marker(dep: str) -> tuple[str, str] | None:
    """Parse dependency with environment marker to extract platform and dependency name."""
    if ";" not in dep:
        return None  # No marker present

    dep_name, marker = dep.split(";", 1)
    dep_name = dep_name.strip()
    marker = marker.strip()

    # Parse platform-specific markers
    if "sys_platform" in marker:
        platform = _extract_platform_from_marker(marker)
        if platform:
            return platform, dep_name

    elif "platform_machine" in marker:
        arch = _extract_architecture_from_marker(marker)
        if arch:
            return f"arch_{arch}", dep_name

    return None


def _extract_platform_from_marker(marker: str) -> str | None:
    """Extract platform from environment marker."""
    # Handle markers like: sys_platform == "win32" or sys_platform == "darwin"
    platform_match = re.search(r'sys_platform\s*==\s*["\']([^"\']+)["\']', marker)
    if platform_match:
        platform = platform_match.group(1)
        # Map to conda platform names
        platform_map = {"win32": "win", "darwin": "osx", "linux": "linux"}
        return platform_map.get(platform, platform)
    return None


def _extract_architecture_from_marker(marker: str) -> str | None:
    """Extract architecture from environment marker."""
    # Handle markers like: platform_machine == "x86_64" or platform_machine == "aarch64"
    arch_match = re.search(r'platform_machine\s*==\s*["\']([^"\']+)["\']', marker)
    if arch_match:
        arch = arch_match.group(1)
        # Map to conda architecture names
        arch_map = {
            "x86_64": "64",
            "amd64": "64",
            "i386": "32",
            "i686": "32",
            "aarch64": "arm64",
            "arm64": "arm64",
        }
        return arch_map.get(arch, arch)
    return None


def _detect_architecture_config(toml: dict) -> dict[str, _t.Any]:
    """Detect architecture-specific configurations."""
    config: dict[str, _t.Any] = {}

    # Check for noarch configuration
    build_system = toml.get("build-system", {})
    if build_system.get("build-backend") in [
        "flit_core.buildapi",
        "poetry.core.masonry.api",
    ]:
        # Pure Python packages are typically noarch
        config["noarch"] = "python"

    # Check for C extensions or compiled code indicators
    project = toml.get("project", {})
    dependencies = project.get("dependencies", [])

    # Look for indicators of compiled dependencies
    compiled_deps = ["numpy", "scipy", "pandas", "tensorflow", "torch", "opencv"]
    has_compiled = any(
        any(comp_dep in dep for comp_dep in compiled_deps) for dep in dependencies
    )

    if has_compiled:
        # Suggest architecture variants for compiled dependencies
        config["arch_variants"] = ["64", "arm64"]

    return config


def _detect_os_config(project: dict) -> dict[str, _t.Any]:
    """Detect OS-specific configurations."""
    config: dict[str, _t.Any] = {}

    # Look for OS-specific dependencies
    classifiers = project.get("classifiers", [])
    supported_os = set()

    for classifier in classifiers:
        if "Operating System ::" in classifier:
            if "Microsoft :: Windows" in classifier:
                supported_os.add("win")
            elif "MacOS" in classifier:
                supported_os.add("osx")
            elif "POSIX :: Linux" in classifier:
                supported_os.add("linux")
            elif "OS Independent" in classifier:
                supported_os.update(["win", "osx", "linux"])

    if supported_os:
        config["supported_platforms"] = sorted(supported_os)

    # Check for platform-specific scripts or URLs
    urls = project.get("urls", {})
    if any("win" in url.lower() or "windows" in url.lower() for url in urls.values()):
        config["has_windows_specific"] = True
    if any("mac" in url.lower() or "darwin" in url.lower() for url in urls.values()):
        config["has_macos_specific"] = True

    return config


def build_package_section(_toml: dict, _project_root: pathlib.Path) -> dict:
    """Build the package section of the recipe."""
    return {
        "name": "${{ name }}",
        "version": _VERSION_TEMPLATE,
    }


def build_about_section(toml: dict, _recipe_dir: pathlib.Path) -> dict:
    """Build the about section of the recipe."""
    project = toml["project"]
    urls = project.get("urls", {}) if isinstance(project.get("urls"), dict) else {}
    urls_norm = {k.lower(): v for k, v in urls.items()}

    homepage = urls_norm.get("homepage") or urls_norm.get("repository")

    # Handle license
    license_info = project.get("license")
    license_value = None
    license_file = None
    if isinstance(license_info, dict):
        if "text" in license_info:
            license_value = license_info["text"]
        elif "file" in license_info:
            license_file = license_info["file"]
            # Try to determine license type from the file content
            license_path = pathlib.Path(license_file)
            if license_path.exists():
                try:
                    with license_path.open("r", encoding="utf-8") as f:
                        content = f.read().lower()
                        if "mit license" in content:
                            license_value = "MIT"
                        elif "apache license" in content and "version 2.0" in content:
                            license_value = "Apache-2.0"
                        elif "bsd license" in content:
                            license_value = "BSD-3-Clause"
                        elif (
                            "gnu general public license" in content
                            and "version 3" in content
                        ):
                            license_value = "GPL-3.0"
                        elif (
                            "gnu general public license" in content
                            and "version 2" in content
                        ):
                            license_value = "GPL-2.0"
                        # Add more license detection as needed
                except (OSError, UnicodeDecodeError):
                    pass  # Keep license_value as None if file can't be read
    elif isinstance(license_info, str):
        license_value = license_info

    # Handle license-files
    license_files = project.get("license-files")
    if license_files:
        # conda expects license_file, can be str or list
        if isinstance(license_files, list):
            license_file = license_files
        else:
            license_file = [license_files]

    # For conda recipes with source path, license files should be relative to source directory
    # not the recipe directory. Since most conda recipes use source: path: .., the license
    # file should just be the filename without any relative path prefix
    if license_file:
        if isinstance(license_file, list):
            # Remove any directory prefixes for conda source builds
            license_file = [pathlib.Path(f).name for f in license_file]
        else:
            # Remove any directory prefixes for conda source builds
            license_file = pathlib.Path(license_file).name

    std_about = {
        "summary": project.get("description", ""),
        "license": license_value,
        "license_file": license_file,
        "homepage": homepage,
        "documentation": urls_norm.get("documentation"),
        "repository": urls_norm.get("repository"),
    }

    # Pick up overrides/additions from tool.conda.recipe.about
    overrides = _toml_get(toml, "tool.conda.recipe.about", {})
    return _merge_dict(std_about, overrides)


def build_source_section(toml: dict) -> dict:
    """Build the source section of the recipe with intelligent auto-detection."""
    # Check for explicit configuration in tool.conda.recipe.source
    explicit_source = _toml_get(toml, "tool.conda.recipe.source")
    if explicit_source:
        return _t.cast(dict, explicit_source)

    # Auto-detect source configuration
    detected_source = _auto_detect_source_section(toml)

    return detected_source


def _auto_detect_source_section(toml: dict) -> dict:
    """Auto-detect source configuration from project metadata."""
    project = toml.get("project", {})
    urls = project.get("urls", {}) if isinstance(project.get("urls"), dict) else {}
    urls_norm = {k.lower(): v for k, v in urls.items()}

    # Try different source detection strategies in order of preference

    # 1. Try to detect Git repository source
    git_source = _detect_git_source(urls_norm)
    if git_source:
        return git_source

    # 2. Try to generate PyPI source URL
    pypi_source = _detect_pypi_source(project)
    if pypi_source:
        return pypi_source

    # 3. Try to detect other URL sources
    url_source = _detect_url_source(urls_norm)
    if url_source:
        return url_source

    # 4. Default to local path
    return {"path": ".."}


def _detect_git_source(urls: dict) -> dict | None:
    """Detect Git repository source from project URLs."""
    git_url = None

    # Look for repository URL in common keys
    for key in ["repository", "source", "homepage"]:
        url = urls.get(key, "")
        if url and _is_git_url(url):
            git_url = url
            break

    if not git_url:
        return None

    # Convert various Git URL formats to standard format
    normalized_url = _normalize_git_url(git_url)

    git_source = {"git": normalized_url}

    # Try to detect branch or tag
    branch_or_tag = _detect_git_ref()
    if branch_or_tag:
        if branch_or_tag.startswith("v") or "." in branch_or_tag:
            git_source["tag"] = branch_or_tag
        else:
            git_source["branch"] = branch_or_tag

    return git_source


def _is_git_url(url: str) -> bool:
    """Check if a URL appears to be a Git repository."""
    git_indicators = [
        "github.com",
        "gitlab.com",
        "bitbucket.org",
        "git@",
        ".git",
        "/git/",
        "sourceforge.net",
        "codeberg.org",
    ]
    return any(indicator in url.lower() for indicator in git_indicators)


def _normalize_git_url(url: str) -> str:
    """Normalize Git URL to a standard format."""
    # Convert SSH to HTTPS for conda recipes
    if url.startswith("git@github.com:"):
        url = url.replace("git@github.com:", "https://github.com/")
    elif url.startswith("git@gitlab.com:"):
        url = url.replace("git@gitlab.com:", "https://gitlab.com/")
    elif url.startswith("git@bitbucket.org:"):
        url = url.replace("git@bitbucket.org:", "https://bitbucket.org/")

    # Remove .git suffix if present
    if url.endswith(".git"):
        url = url[:-4]

    # Remove trailing slash
    url = url.rstrip("/")

    return url


def _detect_git_ref() -> str | None:
    """Try to detect current Git branch or tag."""
    try:
        # First try to get current tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    try:
        # Then try to get current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            # Only return non-main/master branches for reproducibility
            if branch and branch not in ["main", "master", "develop"]:
                return branch
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    return None


def _detect_pypi_source(project: dict) -> dict | None:
    """Generate PyPI source URL from project metadata."""
    name = project.get("name")
    version = project.get("version")

    if not name:
        return None

    # For dynamic version, use template variables
    if version:
        template_version = version
    else:
        # Check if version is dynamic
        dynamic_fields = project.get("dynamic", [])
        if "version" in dynamic_fields:
            template_version = _VERSION_TEMPLATE
        else:
            return None

    # Normalize package name for PyPI
    pypi_name = name.replace("-", "_")
    first_char = name[0].lower()

    pypi_source = {
        "url": f"https://pypi.org/packages/source/{first_char}/{name}/{pypi_name}-{template_version}.tar.gz"
    }

    # Only add sha256 if we have a static version
    if version and version != _VERSION_TEMPLATE:
        _warn(
            f"PyPI source detected for {name} v{version}. Consider adding sha256 checksum manually."
        )

    return pypi_source


def _detect_url_source(urls: dict) -> dict | None:
    """Detect other URL-based sources from project metadata."""
    # Look for download or source URLs
    for key in ["download", "source", "archive", "tarball", "zip"]:
        url = urls.get(key, "")
        if url and _is_archive_url(url):
            return {"url": url}

    return None


def _is_archive_url(url: str) -> bool:
    """Check if URL appears to be a downloadable archive."""
    archive_extensions = [".tar.gz", ".tar.bz2", ".tar.xz", ".zip", ".whl"]
    url_lower = url.lower()
    return any(url_lower.endswith(ext) for ext in archive_extensions)


def _detect_build_script(build_system: dict) -> str:
    """Auto-detect appropriate build script based on build backend."""
    backend = build_system.get("build-backend", "")

    if "poetry" in backend:
        return "poetry build && $PYTHON -m pip install dist/*.whl -vv"
    elif "flit" in backend:
        return "$PYTHON -m flit install"
    elif "hatchling" in backend or "hatch" in backend:
        return "$PYTHON -m pip install . -vv --no-build-isolation"
    else:
        return "$PYTHON -m pip install . -vv --no-build-isolation"


def _detect_entry_points(project: dict) -> list[str]:
    """Auto-detect entry points from project.scripts."""
    project_scripts = project.get("scripts", {})
    if project_scripts:
        return [f"{name} = {target}" for name, target in project_scripts.items()]
    return []


def _detect_skip_conditions(requires_python: str) -> list[str]:
    """Auto-detect skip conditions for Python version constraints."""
    if not requires_python:
        return []

    # Handle cases like ">=3.9", "<3.13", ">=3.9,<4.0"
    min_match = re.search(r">=\s*(\d+)\.(\d+)", requires_python)
    max_match = re.search(r"<\s*(\d+)\.(\d+)", requires_python)

    skip_conditions = []
    if min_match:
        min_major, min_minor = min_match.groups()
        # Skip versions below minimum
        skip_conditions.append(f"py<{min_major}{min_minor}")

    if max_match:
        max_major, max_minor = max_match.groups()
        # Skip versions at or above maximum
        skip_conditions.append(f"py>={max_major}{max_minor}")

    return skip_conditions


def build_build_section(toml: dict) -> dict:
    """Build the build section of the recipe with enhanced auto-detection."""
    # Get configuration from tool.conda.recipe.build
    section = _toml_get(toml, "tool.conda.recipe.build", {})

    # Enhanced defaults and auto-detection
    if "script" not in section:
        build_system = toml.get("build-system", {})
        section["script"] = _detect_build_script(build_system)

    if "number" not in section:
        section["number"] = 0

    # Auto-detect entry points from project.scripts
    if "entry_points" not in section:
        project = toml.get("project", {})
        entry_points = _detect_entry_points(project)
        if entry_points:
            section["entry_points"] = entry_points

    # Auto-detect skip conditions for Python version constraints
    if "skip" not in section:
        requires_python = toml.get("project", {}).get("requires-python", "")
        skip_conditions = _detect_skip_conditions(requires_python)
        if skip_conditions:
            section["skip"] = skip_conditions

    return _t.cast(dict, section)


def _convert_python_version_marker(dep_name: str, marker: str) -> dict | str:
    """Convert Python version markers to conda selectors."""
    if "python_version" in marker:
        if "<" in marker:
            # Extract version like python_version < "3.11"
            version_match = re.search(r'["\'](\d+\.\d+)["\']', marker)
            if version_match:
                version = version_match.group(1)
                version_no_dot = version.replace(".", "")
                return {"if": f"py<{version_no_dot}", "then": [dep_name]}
        elif ">=" in marker:
            # Extract version like python_version >= "3.11"
            version_match = re.search(r'["\'](\d+\.\d+)["\']', marker)
            if version_match:
                version = version_match.group(1)
                version_no_dot = version.replace(".", "")
                return {"if": f"py>={version_no_dot}", "then": [dep_name]}

    # For unsupported markers, include the dependency unconditionally with a warning
    _warn(
        f"Unsupported environment marker '{marker}' for dependency '{dep_name}', including unconditionally"
    )
    return dep_name


def _process_conditional_dependencies(deps: list[str]) -> list[str | dict]:
    """Process dependencies with environment markers and convert to conda selectors."""
    processed_deps = []

    for dep in deps:
        if ";" in dep:  # Environment marker
            dep_name, marker = dep.split(";", 1)
            dep_name = dep_name.strip()
            marker = marker.strip()

            converted = _convert_python_version_marker(dep_name, marker)
            processed_deps.append(converted)
        else:
            processed_deps.append(dep)

    return processed_deps


def _process_optional_dependencies(
    optional_deps: dict, context: dict
) -> dict[str, list[str | dict]]:
    """Process optional dependencies for potential use in outputs or variants."""
    processed = {}

    for extra_name, extra_deps in optional_deps.items():
        # Normalize the dependencies
        normalized_deps = _normalize_deps(extra_deps)
        # Process conditional dependencies
        processed_deps = _process_conditional_dependencies(normalized_deps)
        processed[extra_name] = processed_deps

    return processed


def _dedupe_mixed_requirements(
    combined: list[str | dict],
) -> list[str | dict]:
    """Deduplicate requirements list containing both strings and dicts."""
    seen = set()
    deduped: list[str | dict] = []

    for item in combined:
        if isinstance(item, str):
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        else:
            # For dict items (selectors), include them as-is
            deduped.append(item)

    return deduped


def build_requirements_section(toml: dict, context: dict) -> dict:
    """Build the requirements section with enhanced dependency handling."""
    # Get python_min and python_max from context for consistent python version handling
    python_min = context.get("python_min", "")
    python_max = context.get("python_max", "")

    # Build python spec with min and optionally max version
    if python_min and python_max:
        python_spec = f"python >={python_min},<{python_max}"
    elif python_min:
        python_spec = f"python >={python_min}"
    else:
        python_spec = "python"

    reqs: dict[str, list[str | dict]] = {"build": [], "host": [], "run": []}

    if "tool" in toml and "pixi" in toml["tool"]:
        pixi = toml["tool"]["pixi"]
        # Build deps - normalize from dict/list to list
        build_deps = pixi.get("feature", {}).get("build", {}).get("dependencies", {})
        build_normalized = _t.cast(list[Union[str, dict]], _normalize_deps(build_deps))
        reqs["build"] = build_normalized
        # Host deps - normalize from dict/list to list
        host_deps = pixi.get("host-dependencies", {})
        host_normalized = _t.cast(list[Union[str, dict]], _normalize_deps(host_deps))
        host_normalized.insert(0, python_spec)
        reqs["host"] = host_normalized
    else:
        _warn(
            "Pixi configuration not found; `build` and `host` requirement sections "
            "must be provided via tool.conda.recipe.requirements"
        )

    # Runtime deps from PEP 621 with enhanced processing
    project = toml.get("project", {})
    dependencies = project.get("dependencies", [])

    # Process conditional dependencies
    processed_run_deps = _process_conditional_dependencies(dependencies)
    processed_run_deps.insert(0, python_spec)
    reqs["run"] = processed_run_deps

    # Store optional dependencies for potential use (not added to main requirements by default)
    optional_deps = project.get("optional-dependencies", {})
    if optional_deps:
        # This could be used later for multi-output packages or variants
        context["optional_dependencies"] = _process_optional_dependencies(
            optional_deps, context
        )

    # Allow recipe-specific overrides/additions
    recipe_reqs = _toml_get(toml, "tool.conda.recipe.requirements", {})
    for sec in ("build", "host", "run"):
        base_reqs = reqs.get(sec, [])
        extra_reqs_normalized = _normalize_deps(recipe_reqs.get(sec, []))
        # Process conditional dependencies for extra requirements too
        if sec == "run":
            extra_reqs_processed = _process_conditional_dependencies(
                extra_reqs_normalized
            )
        else:
            extra_reqs_processed = _t.cast(
                list[Union[str, dict]], extra_reqs_normalized
            )
        # Combine and dedupe while preserving order and handling mixed types
        combined = base_reqs + extra_reqs_processed
        reqs[sec] = _dedupe_mixed_requirements(combined)

    return reqs


def build_test_section(toml: dict) -> dict | None:
    """Build the test section of the recipe with intelligent auto-detection."""
    # First check if there's explicit test configuration
    explicit_test = _toml_get(toml, "tool.conda.recipe.test")
    if explicit_test:
        return _t.cast(dict, explicit_test)

    # Auto-detect test requirements and commands
    test_section = _auto_detect_test_section(toml)

    return test_section if test_section else None


def _auto_detect_test_section(toml: dict) -> dict | None:
    """Auto-detect test configuration from project structure and dependencies."""
    test_config: dict[str, _t.Any] = {}

    # Detect test imports
    imports = _detect_test_imports(toml)
    if imports:
        test_config["python"] = {"imports": imports}

    # Detect test commands
    commands = _detect_test_commands(toml)
    if commands:
        if "python" not in test_config:
            test_config["python"] = {}
        test_config["python"]["commands"] = commands

    # Detect test requirements
    requires = _detect_test_requirements(toml)
    if requires:
        test_config["requires"] = requires

    return test_config if test_config else None


def _detect_test_imports(toml: dict) -> list[str]:
    """Detect test imports based on project package name and structure."""
    imports = []

    # Get main package name
    project = toml.get("project", {})
    package_name = project.get("name", "").replace("-", "_")

    if package_name:
        imports.append(package_name)

    # Check for common test packages in dependencies
    deps_to_check = [
        project.get("dependencies", []),
        project.get("optional-dependencies", {}).get("test", []),
        project.get("optional-dependencies", {}).get("testing", []),
    ]

    for deps in deps_to_check:
        if isinstance(deps, list):
            for dep in deps:
                dep_name = (
                    dep.split()[0]
                    .split(">=")[0]
                    .split("==")[0]
                    .split("<")[0]
                    .split(">")[0]
                )
                if dep_name in _TEST_PACKAGES:
                    imports.append(dep_name)

    # Remove duplicates while preserving order
    seen = set()
    unique_imports = []
    for imp in imports:
        if imp not in seen:
            seen.add(imp)
            unique_imports.append(imp)

    return unique_imports


# Test detection constants
_PYTEST_CMD = "python -m pytest"
_UNITTEST_CMD = "python -m unittest discover"
_TEST_PACKAGES = {"pytest", "unittest", "unittest2", "nose", "nose2"}
_TEST_GROUPS = ["test", "testing", "tests", "dev", "development"]

# Template constants
_VERSION_TEMPLATE = "${{ version }}"


def _detect_test_commands(toml: dict) -> list[str]:
    """Detect test commands from project configuration."""
    commands = []

    # Check for pytest configuration
    if _has_pytest_config(toml):
        commands.append(_PYTEST_CMD)

    # Check for test commands in scripts
    script_commands = _detect_script_test_commands(toml)
    commands.extend(script_commands)

    # Check for test frameworks in dependencies
    framework_commands = _detect_framework_commands(toml, commands)
    commands.extend(framework_commands)

    # Check hatch environment scripts
    hatch_commands = _detect_hatch_test_commands(toml)
    commands.extend(hatch_commands)

    return commands


def _has_pytest_config(toml: dict) -> bool:
    """Check if pytest is configured in the project."""
    return "tool" in toml and "pytest" in toml["tool"]


def _detect_script_test_commands(toml: dict) -> list[str]:
    """Detect test commands from project scripts."""
    commands = []
    project = toml.get("project", {})
    scripts = project.get("scripts", {})

    for script_name, script_cmd in scripts.items():
        if "test" in script_name.lower() or "pytest" in script_cmd:
            commands.append(f"python -m {script_cmd}")

    return commands


def _detect_framework_commands(toml: dict, existing_commands: list[str]) -> list[str]:
    """Detect test framework commands from dependencies."""
    commands = []

    # Get all dependencies
    project = toml.get("project", {})
    deps = project.get("dependencies", [])
    optional_deps = project.get("optional-dependencies", {})

    all_deps = deps[:]
    for extra_deps in optional_deps.values():
        if isinstance(extra_deps, list):
            all_deps.extend(extra_deps)

    # Check for test frameworks
    has_pytest = any("pytest" in dep for dep in all_deps)
    has_unittest = any("unittest" in dep for dep in all_deps)

    if has_pytest and _PYTEST_CMD not in existing_commands:
        commands.append(_PYTEST_CMD)
    elif has_unittest and not existing_commands:
        commands.append(_UNITTEST_CMD)

    return commands


def _detect_hatch_test_commands(toml: dict) -> list[str]:
    """Detect test commands from hatch environment configuration."""
    commands: list[str] = []

    if "tool" not in toml or "hatch" not in toml["tool"]:
        return commands

    hatch_envs = toml["tool"]["hatch"].get("envs", {})
    for env_name, env_config in hatch_envs.items():
        if "test" in env_name.lower():
            scripts = env_config.get("scripts", {})
            for script_cmd in scripts.values():
                if isinstance(script_cmd, str) and script_cmd not in commands:
                    commands.append(script_cmd)

    return commands


def _detect_test_requirements(toml: dict) -> list[str]:
    """Detect test requirements from optional dependencies."""
    test_requires = []

    project = toml.get("project", {})
    optional_deps = project.get("optional-dependencies", {})

    for group_name, deps in optional_deps.items():
        if group_name.lower() in _TEST_GROUPS and isinstance(deps, list):
            for dep in deps:
                # Convert pip-style to conda-style
                conda_dep = dep.replace("_", "-").split(";")[0].strip()
                if conda_dep not in test_requires:
                    test_requires.append(conda_dep)

    # Add common test tools if not already present
    has_pytest = any("pytest" in req for req in test_requires)
    if not has_pytest:
        # Check if pytest is in main dependencies
        main_deps = project.get("dependencies", [])
        if any("pytest" in dep for dep in main_deps):
            test_requires.append("pytest")

    return test_requires


def build_extra_section(toml: dict) -> dict | None:
    """Build the extra section of the recipe."""
    result = _toml_get(toml, "tool.conda.recipe.extra")
    return _t.cast(dict, result) if result is not None else None


# ----
# Main Recipe Assembly
# ----


def assemble_recipe(
    toml: dict, project_root: pathlib.Path, recipe_dir: pathlib.Path
) -> dict:
    """
    Assemble the complete recipe from the TOML configuration.

    Args:
        toml: Parsed pyproject.toml data
        project_root: Path to the project root directory
        recipe_dir: Path to the recipe output directory

    Returns:
        Complete recipe dictionary
    """
    # Build recipe in the specified order: context, package, source, build, requirements, test, about, extra
    recipe: dict[str, _t.Any] = {}

    context = build_context_section(toml, project_root)
    recipe["context"] = context
    recipe["package"] = build_package_section(toml, project_root)
    recipe["source"] = build_source_section(toml)
    recipe["build"] = build_build_section(toml)
    recipe["requirements"] = build_requirements_section(toml, context)

    test_section = build_test_section(toml)
    if test_section:
        recipe["test"] = test_section

    recipe["about"] = build_about_section(toml, recipe_dir)

    extra_section = build_extra_section(toml)
    if extra_section:
        recipe["extra"] = extra_section

    return recipe


def load_pyproject_toml(pyproject_path: pathlib.Path) -> dict:
    """
    Load and parse a pyproject.toml file.

    Args:
        pyproject_path: Path to the pyproject.toml file

    Returns:
        Parsed TOML data as dictionary

    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist
        tomllib.TOMLDecodeError: If TOML is malformed
    """
    if not pyproject_path.exists():
        raise FileNotFoundError(f"{pyproject_path} not found")

    with pyproject_path.open("rb") as fh:
        return _t.cast(dict, tomllib.load(fh))


def write_recipe_yaml(
    recipe_dict: dict, output_path: pathlib.Path, overwrite: bool = False
) -> None:
    """
    Write the recipe dictionary to a YAML file.

    Args:
        recipe_dict: The recipe dictionary to write
        output_path: Path where to write the recipe.yaml
        overwrite: If True, overwrite existing files. If False, backup existing files.
    """
    # Use enhanced output customization
    output_config = OutputConfig()
    write_recipe_with_config(recipe_dict, output_path, output_config, overwrite)


def write_recipe_with_config(
    recipe_dict: dict,
    output_path: pathlib.Path,
    config: OutputConfig,
    overwrite: bool = False,
) -> None:
    """
    Write the recipe dictionary to a file with customization options.

    Args:
        recipe_dict: The recipe dictionary to write
        output_path: Path where to write the recipe file
        config: Output configuration options
        overwrite: If True, overwrite existing files. If False, backup existing files.
    """
    # Create parent directories if they don't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Backup existing file if it exists and overwrite is not specified
    if output_path.exists() and not overwrite:
        backup_path = output_path.with_suffix(output_path.suffix + ".bak")
        output_path.replace(backup_path)
        print(f"⚠ Existing {output_path} backed up to {backup_path}")

    # Apply output customizations
    customized_recipe = _apply_output_customizations(recipe_dict, config)

    # Validate output if requested
    if config.validate_output:
        _validate_recipe_output(customized_recipe, config)

    # Write in the specified format
    if config.output_format == "yaml":
        _write_yaml_output(customized_recipe, output_path, config)
    elif config.output_format == "json":
        _write_json_output(customized_recipe, output_path, config)
    else:
        raise ValueError(f"Unsupported output format: {config.output_format}")


class OutputConfig:
    """Configuration class for output customization."""

    def __init__(
        self,
        output_format: str = "yaml",
        yaml_style: str = "default",
        include_comments: bool = True,
        sort_keys: bool = False,
        indent: int = 2,
        validate_output: bool = True,
        include_sections: list[str] | None = None,
        exclude_sections: list[str] | None = None,
        custom_templates: dict[str, str] | None = None,
        json_indent: int = 2,
    ):
        """
        Initialize output configuration.

        Args:
            output_format: Output format ('yaml' or 'json')
            yaml_style: YAML style ('default', 'block', 'flow')
            include_comments: Whether to include helpful comments
            sort_keys: Whether to sort dictionary keys
            indent: Number of spaces for indentation
            validate_output: Whether to validate the output
            include_sections: Specific sections to include (None = all)
            exclude_sections: Sections to exclude
            custom_templates: Custom templates for sections
            json_indent: Indentation for JSON output
        """
        self.output_format = output_format
        self.yaml_style = yaml_style
        self.include_comments = include_comments
        self.sort_keys = sort_keys
        self.indent = indent
        self.validate_output = validate_output
        self.include_sections = include_sections or []
        self.exclude_sections = exclude_sections or []
        self.custom_templates = custom_templates or {}
        self.json_indent = json_indent


def _apply_output_customizations(recipe_dict: dict, config: OutputConfig) -> dict:
    """Apply output customizations to the recipe dictionary."""
    result = recipe_dict.copy()

    # Apply section filtering
    if config.include_sections:
        # Only include specified sections
        filtered = {}
        for section in config.include_sections:
            if section in result:
                filtered[section] = result[section]
        result = filtered

    if config.exclude_sections:
        # Exclude specified sections
        for section in config.exclude_sections:
            result.pop(section, None)

    # Apply custom templates
    for section, template in config.custom_templates.items():
        if section in result:
            result[section] = _apply_template(result[section], template)

    # Add helpful comments if requested
    if config.include_comments:
        result = _add_helpful_comments(result)

    return result


def _apply_template(section_data: _t.Any, template: str) -> _t.Any:
    """Apply a custom template to section data."""
    # For now, return the original data
    # This could be enhanced to support template substitution
    return section_data


def _add_helpful_comments(recipe_dict: dict) -> dict:
    """Add helpful comments to the recipe dictionary."""
    # YAML comments would require a different YAML library (like ruamel.yaml)
    # For now, we'll add special comment keys that could be processed later
    commented = recipe_dict.copy()

    # Add helpful metadata
    if "context" in commented:
        # Could add comments about context variable usage
        pass

    if "requirements" in commented:
        # Could add comments about requirement sources
        pass

    return commented


def _validate_recipe_output(recipe_dict: dict, _config: OutputConfig) -> None:
    """Validate the recipe output against known schema requirements."""
    required_sections = ["package", "source", "build", "requirements"]
    missing_sections = []

    for section in required_sections:
        if section not in recipe_dict:
            missing_sections.append(section)

    if missing_sections:
        print(f"⚠ Warning: Missing recommended sections: {', '.join(missing_sections)}")

    # Validate package section
    if "package" in recipe_dict:
        package = recipe_dict["package"]
        if not package.get("name"):
            print("⚠ Warning: Package name is missing")
        if not package.get("version"):
            print("⚠ Warning: Package version is missing")

    # Validate context variables
    if "context" in recipe_dict:
        _validate_context_variables(recipe_dict)


def _validate_context_variables(recipe_dict: dict) -> None:
    """Validate that context variables are properly referenced."""
    context = recipe_dict.get("context", {})
    context_vars = set(context.keys())

    # Find template references in the recipe
    template_refs = _find_template_references(recipe_dict)

    # Check for undefined context variables
    undefined_vars = template_refs - context_vars
    if undefined_vars:
        print(f"⚠ Warning: Undefined context variables: {', '.join(undefined_vars)}")

    # Check for unused context variables
    unused_vars = context_vars - template_refs
    if unused_vars:
        print(f"ℹ Info: Unused context variables: {', '.join(unused_vars)}")


def _find_template_references(obj: _t.Any, refs: set[str] | None = None) -> set[str]:
    """Find all template variable references in the recipe."""
    if refs is None:
        refs = set()

    if isinstance(obj, str):
        # Find ${{ variable }} patterns
        import re

        pattern = r"\$\{\{\s*(\w+)\s*\}\}"
        matches = re.findall(pattern, obj)
        refs.update(matches)
    elif isinstance(obj, dict):
        for value in obj.values():
            _find_template_references(value, refs)
    elif isinstance(obj, list):
        for item in obj:
            _find_template_references(item, refs)

    return refs


def _write_yaml_output(
    recipe_dict: dict, output_path: pathlib.Path, config: OutputConfig
) -> None:
    """Write recipe as YAML with custom formatting."""
    with output_path.open("w", encoding="utf-8") as fh:
        if config.yaml_style == "block":
            yaml.safe_dump(
                recipe_dict,
                fh,
                default_flow_style=False,
                sort_keys=config.sort_keys,
                indent=config.indent,
            )
        else:
            yaml.safe_dump(
                recipe_dict,
                fh,
                default_flow_style=(config.yaml_style == "flow"),
                sort_keys=config.sort_keys,
                indent=config.indent,
            )


def _write_json_output(
    recipe_dict: dict, output_path: pathlib.Path, config: OutputConfig
) -> None:
    """Write recipe as JSON with custom formatting."""
    import json

    # Change extension to .json if it's .yaml/.yml
    if output_path.suffix.lower() in [".yaml", ".yml"]:
        output_path = output_path.with_suffix(".json")

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(
            recipe_dict,
            fh,
            indent=config.json_indent,
            sort_keys=config.sort_keys,
            ensure_ascii=False,
        )


def generate_recipe(
    pyproject_path: pathlib.Path, output_path: pathlib.Path, overwrite: bool = False
) -> None:
    """
    Generate a Rattler-Build recipe.yaml from a pyproject.toml file.

    Args:
        pyproject_path: Path to the input pyproject.toml file
        output_path: Path for the output recipe.yaml file
        overwrite: Whether to overwrite existing output files
    """
    toml_data = load_pyproject_toml(pyproject_path)
    recipe_dict = assemble_recipe(toml_data, pyproject_path.parent, output_path.parent)

    # Check for output customization configuration
    output_config = _load_output_config(toml_data)

    write_recipe_with_config(recipe_dict, output_path, output_config, overwrite)
    print(f"✔ Wrote {output_path}")


def generate_recipe_with_config(
    pyproject_path: pathlib.Path,
    output_path: pathlib.Path,
    config: OutputConfig,
    overwrite: bool = False,
) -> None:
    """
    Generate a Rattler-Build recipe with custom output configuration.

    Args:
        pyproject_path: Path to the input pyproject.toml file
        output_path: Path for the output recipe file
        config: Output configuration options
        overwrite: Whether to overwrite existing output files
    """
    toml_data = load_pyproject_toml(pyproject_path)
    recipe_dict = assemble_recipe(toml_data, pyproject_path.parent, output_path.parent)

    write_recipe_with_config(recipe_dict, output_path, config, overwrite)
    print(f"✔ Wrote {output_path} with custom configuration")


def _load_output_config(toml_data: dict) -> OutputConfig:
    """Load output configuration from pyproject.toml."""
    # Check for output customization in tool.conda.recipe.output
    output_settings = _toml_get(toml_data, "tool.conda.recipe.output", {})

    return OutputConfig(
        output_format=output_settings.get("format", "yaml"),
        yaml_style=output_settings.get("yaml_style", "default"),
        include_comments=output_settings.get("include_comments", True),
        sort_keys=output_settings.get("sort_keys", False),
        indent=output_settings.get("indent", 2),
        validate_output=output_settings.get("validate_output", True),
        include_sections=output_settings.get("include_sections"),
        exclude_sections=output_settings.get("exclude_sections"),
        custom_templates=output_settings.get("custom_templates"),
        json_indent=output_settings.get("json_indent", 2),
    )
