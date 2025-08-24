"""
Tests for the demo module.
"""

import pytest

from pyrattler_recipe_autogen.demo import (
    create_demo_pyproject,
    demo_scientific_package,
    demo_simple_package,
    demo_webapp_package,
    generate_recipe_from_data,
)


def test_create_demo_pyproject_simple():
    """Test creation of simple demo project data."""
    data = create_demo_pyproject("simple")
    assert data["project"]["name"] == "demo-package"
    assert "numpy>=1.20.0" in data["project"]["dependencies"]
    assert "hatchling" in data["build-system"]["requires"]


def test_create_demo_pyproject_scientific():
    """Test creation of scientific demo project data."""
    data = create_demo_pyproject("scientific")
    assert data["project"]["name"] == "scientific-demo"
    assert "scipy>=1.7.0" in data["project"]["dependencies"]
    assert "setuptools>=64" in data["build-system"]["requires"]


def test_create_demo_pyproject_webapp():
    """Test creation of webapp demo project data."""
    data = create_demo_pyproject("webapp")
    assert data["project"]["name"] == "webapp-demo"
    assert "fastapi>=0.68.0" in data["project"]["dependencies"]
    assert "poetry-core>=1.0.0" in data["build-system"]["requires"]


def test_create_demo_pyproject_unknown():
    """Test handling of unknown demo type."""
    data = create_demo_pyproject("unknown-type")
    # Should default to simple
    assert data["project"]["name"] == "demo-package"


def test_generate_recipe_from_data():
    """Test recipe generation from demo data."""
    data = create_demo_pyproject("simple")
    recipe = generate_recipe_from_data(data)

    # Check basic YAML structure
    assert "context:" in recipe
    assert "package:" in recipe
    assert "source:" in recipe
    assert "build:" in recipe
    assert "requirements:" in recipe
    assert "test:" in recipe
    assert "about:" in recipe

    # Check specific content
    assert "demo-package" in recipe
    assert "numpy" in recipe
    assert "pandas" in recipe


def test_demo_simple_package():
    """Test simple package demo generation."""
    recipe = demo_simple_package()
    assert isinstance(recipe, str)
    assert "demo-package" in recipe
    assert "context:" in recipe


def test_demo_scientific_package():
    """Test scientific package demo generation."""
    recipe = demo_scientific_package()
    assert isinstance(recipe, str)
    assert "scientific-demo" in recipe
    assert "scipy" in recipe


def test_demo_webapp_package():
    """Test webapp package demo generation."""
    recipe = demo_webapp_package()
    assert isinstance(recipe, str)
    assert "webapp-demo" in recipe
    assert "fastapi" in recipe


@pytest.mark.parametrize("demo_type", ["simple", "scientific", "webapp"])
def test_demo_functions_return_valid_yaml(demo_type):
    """Test that all demo functions return valid YAML."""
    if demo_type == "simple":
        recipe = demo_simple_package()
    elif demo_type == "scientific":
        recipe = demo_scientific_package()
    elif demo_type == "webapp":
        recipe = demo_webapp_package()

    # Try to parse as YAML
    import yaml

    parsed = yaml.safe_load(recipe)
    assert isinstance(parsed, dict)
    assert "package" in parsed
    assert "name" in parsed["package"]
