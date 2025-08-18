"""
Tests for package initialization and imports.
"""

import pytest


def test_package_imports():
    """Test that all public functions can be imported from the package."""
    from pyrattler_recipe_autogen import (
        __version__,
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

    # Test that all imports work
    assert __version__ is not None
    assert callable(assemble_recipe)
    assert callable(build_about_section)
    assert callable(build_build_section)
    assert callable(build_context_section)
    assert callable(build_extra_section)
    assert callable(build_package_section)
    assert callable(build_requirements_section)
    assert callable(build_source_section)
    assert callable(build_test_section)
    assert callable(generate_recipe)
    assert callable(load_pyproject_toml)
    assert callable(resolve_dynamic_version)
    assert callable(write_recipe_yaml)


def test_version_fallback():
    """Test version fallback when _version module is not available."""
    # Mock ImportError for _version module
    import sys
    from unittest.mock import patch

    # Temporarily remove the _version module from sys.modules if it exists
    original_version_module = sys.modules.get("pyrattler_recipe_autogen._version")
    if "pyrattler_recipe_autogen._version" in sys.modules:
        del sys.modules["pyrattler_recipe_autogen._version"]

    try:
        # Mock the import to raise ImportError
        with patch.dict("sys.modules", {"pyrattler_recipe_autogen._version": None}):
            # Force reimport of the package to trigger the fallback
            if "pyrattler_recipe_autogen" in sys.modules:
                del sys.modules["pyrattler_recipe_autogen"]

            # This will trigger the ImportError and fallback
            import pyrattler_recipe_autogen

            # Should use fallback version
            assert pyrattler_recipe_autogen.__version__ == "dev"
    finally:
        # Restore the original state
        if original_version_module is not None:
            sys.modules["pyrattler_recipe_autogen._version"] = original_version_module


def test_all_exports():
    """Test that __all__ contains all the expected exports."""
    import pyrattler_recipe_autogen

    expected_exports = [
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

    assert hasattr(pyrattler_recipe_autogen, "__all__")
    assert set(pyrattler_recipe_autogen.__all__) == set(expected_exports)


if __name__ == "__main__":
    pytest.main([__file__])
