"""
Tests for the demo module.
"""

import sys
from pathlib import Path

import pytest

from pyrattler_recipe_autogen import demo
from pyrattler_recipe_autogen.demo import (
    create_demo_pyproject,
    demo_scientific_package,
    demo_simple_package,
    demo_webapp_package,
    generate_recipe_from_data,
)


def test_main_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["demo.py", "--type", "unknown"])
    with pytest.raises(SystemExit) as excinfo:
        demo.main()
    assert excinfo.value.code == 2


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


def test_print_demo_header(capsys):
    from pyrattler_recipe_autogen.demo import print_demo_header

    print_demo_header("Test Header")
    out = capsys.readouterr().out
    assert "Test Header" in out


def test_print_recipe_preview_short(capsys):
    from pyrattler_recipe_autogen.demo import print_recipe_preview

    recipe = "line1\nline2"
    print_recipe_preview(recipe, max_lines=10)
    out = capsys.readouterr().out
    assert "line1" in out and "line2" in out


def test_print_recipe_preview_long(capsys):
    from pyrattler_recipe_autogen.demo import print_recipe_preview

    recipe = "\n".join([f"line{i}" for i in range(50)])
    print_recipe_preview(recipe, max_lines=5)
    out = capsys.readouterr().out
    assert "showing first 5 lines" in out


def test_run_demo_full(monkeypatch, capsys):
    from pyrattler_recipe_autogen import demo

    monkeypatch.setattr("sys.argv", ["demo.py", "--type", "all", "--full"])
    demo.main()
    out = capsys.readouterr().out
    assert "Demo complete" in out


def test_run_demo_current(monkeypatch, capsys, tmp_path):
    from pyrattler_recipe_autogen import demo

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""
    [project]
    name = "test-demo"
    version = "0.1.0"
    """)
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    monkeypatch.setattr("sys.argv", ["demo.py", "--type", "current"])
    demo.main()
    out = capsys.readouterr().out
    assert "test-demo" in out
