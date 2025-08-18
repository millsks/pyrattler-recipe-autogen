"""
pyrattler-recipe-autogen: Generate Rattler-Build recipe.yaml from pyproject.toml

This package provides tools to automatically generate conda recipe files from Python
projects that use pyproject.toml for configuration.
"""

try:
    from ._version import __version__
except ImportError:
    # Fallback for development installations
    __version__ = "dev"

from .core import (
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

__all__ = [
    "__version__",
    "assemble_recipe",
    "build_about_section", 
    "build_build_section",
    "build_context_section",
    "build_extra_section",
    "build_package_section",
    "build_requirements_section",
    "build_source_section",
    "build_test_section",
    "generate_recipe",
    "load_pyproject_toml",
    "resolve_dynamic_version",
    "write_recipe_yaml",
]
