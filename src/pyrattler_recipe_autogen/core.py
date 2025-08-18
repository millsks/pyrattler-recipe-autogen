"""
Core business logic for generating Rattler-Build recipe.yaml from pyproject.toml

• Pulls canonical project data from `[project]`
• Handles dynamic version resolution from build backends
• If `[tool.pixi]` exists, uses Pixi tables for requirement mapping
• Reads extra/override keys from `[tool.conda.recipe.*]`
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import typing as _t

try:
    import tomllib  # Python ≥3.11
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

try:
    import setuptools_scm
except ImportError:
    setuptools_scm = None

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
            common = pathlib.Path(os.path.commonpath([file_path, recipe_dir]))

            # Get path from recipe_dir back to common ancestor
            recipe_to_common = recipe_dir.relative_to(common)

            # Get path from common ancestor to file
            common_to_file = file_path.relative_to(common)

            # Build relative path: go up from recipe_dir to common, then down to file
            up_dirs = [".."] * len(recipe_to_common.parts)
            relative_path = pathlib.Path(*up_dirs) / common_to_file

            return str(relative_path)
        except (ValueError, OSError):
            # Fallback: return absolute path if all else fails
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
        if setuptools_scm is not None:
            try:
                return str(setuptools_scm.get_version(root=project_root))
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
    """Build the context section of the recipe."""
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

    # Merge in extra context from tool.conda.recipe.extra_context
    # This will override python_min if explicitly provided
    extra_context = _toml_get(toml, "tool.conda.recipe.extra_context", {})
    context.update(extra_context)

    return context


def build_package_section(toml: dict, project_root: pathlib.Path) -> dict:
    """Build the package section of the recipe."""
    return {
        "name": "${{ name }}",
        "version": "${{ version }}",
    }


def build_about_section(toml: dict, recipe_dir: pathlib.Path) -> dict:
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
    """Build the source section of the recipe."""
    # Check for configuration in tool.conda.recipe.source
    section = _toml_get(toml, "tool.conda.recipe.source")
    if section is None:
        # Default to path: .. if configuration is missing
        section = {"path": ".."}
    return _t.cast(dict, section)


def build_build_section(toml: dict) -> dict:
    """Build the build section of the recipe."""
    # Get configuration from tool.conda.recipe.build
    section = _toml_get(toml, "tool.conda.recipe.build", {})

    # Apply defaults for missing fields
    if "script" not in section:
        section["script"] = "$PYTHON -m pip install . -vv --no-build-isolation"

    if "number" not in section:
        section["number"] = 0

    # Note: string fields are left out if missing (no default applied)

    return _t.cast(dict, section)


def build_requirements_section(toml: dict, context: dict) -> dict:
    """Build the requirements section of the recipe."""
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

    reqs: dict[str, list[str]] = {"build": [], "host": [], "run": []}

    if "tool" in toml and "pixi" in toml["tool"]:
        pixi = toml["tool"]["pixi"]
        # Build deps - normalize from dict/list to list
        build_deps = pixi.get("feature", {}).get("build", {}).get("dependencies", {})
        reqs["build"] = _normalize_deps(build_deps)
        # Host deps - normalize from dict/list to list
        host_deps = pixi.get("host-dependencies", {})
        reqs["host"] = _normalize_deps(host_deps)
        reqs["host"].insert(0, python_spec)
    else:
        _warn(
            "Pixi configuration not found; `build` and `host` requirement sections "
            "must be provided via tool.conda.recipe.requirements"
        )

    # Runtime deps from PEP 621
    run_deps = _normalize_deps(toml["project"].get("dependencies", []))
    run_deps.insert(0, python_spec)
    reqs["run"] = run_deps

    # Allow recipe-specific overrides/additions
    recipe_reqs = _toml_get(toml, "tool.conda.recipe.requirements", {})
    for sec in ("build", "host", "run"):
        base_reqs = reqs.get(sec, [])
        extra_reqs = _normalize_deps(recipe_reqs.get(sec, []))
        reqs[sec] = list(dict.fromkeys(base_reqs + extra_reqs))  # dedupe & keep order
    return reqs


def build_test_section(toml: dict) -> dict | None:
    """Build the test section of the recipe."""
    result = _toml_get(toml, "tool.conda.recipe.test")
    return _t.cast(dict, result) if result is not None else None


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
    # Create parent directories if they don't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Backup existing file if it exists and overwrite is not specified
    if output_path.exists() and not overwrite:
        backup_path = output_path.with_suffix(output_path.suffix + ".bak")
        output_path.replace(backup_path)
        print(f"⚠ Existing {output_path} backed up to {backup_path}")

    with output_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(recipe_dict, fh, sort_keys=False)


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
    write_recipe_yaml(recipe_dict, output_path, overwrite)
    print(f"✔ Wrote {output_path}")
