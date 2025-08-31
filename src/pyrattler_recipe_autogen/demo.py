"""
Demo module for pyrattler-recipe-autogen.

This module provides easy-to-run demonstrations of the package functionality,
allowing users to quickly see what the generated recipes look like for different
types of Python projects.

Usage:
    python -m pyrattler_recipe_autogen.demo

    # Or programmatically:
    from pyrattler_recipe_autogen.demo import run_demo, demo_simple_package
    run_demo()
"""

import importlib.util
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Optional

if importlib.util.find_spec("tomllib") is not None:
    import tomllib
    # safe to use tomllib.load(...)
else:
    import tomli as tomllib  # fallback for older Python  # noqa: F401

# Always use toml for writing
import toml
import yaml

from .core import assemble_recipe, load_pyproject_toml

# Constants to avoid duplication
README_FILE = "README.md"
PYTEST_VERSION = "pytest>=6.0"
PYTHON_3_CLASSIFIER = "Programming Language :: Python :: 3"
TOML_SUFFIX = ".toml"


def create_demo_pyproject(demo_type: str = "simple") -> dict[str, Any]:
    """Create sample pyproject.toml content for different demo scenarios."""

    demos = {
        "simple": {
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
            "project": {
                "name": "demo-package",
                "version": "0.1.0",
                "description": "A simple demo package for pyrattler-recipe-autogen",
                "readme": README_FILE,
                "license": {"text": "MIT"},
                "authors": [{"name": "Demo Author", "email": "demo@example.com"}],
                "requires-python": ">=3.9",
                "dependencies": ["numpy>=1.20.0", "pandas>=1.3.0"],
                "optional-dependencies": {
                    "dev": [PYTEST_VERSION, "black", "mypy"],
                    "docs": ["sphinx", "sphinx-rtd-theme"],
                },
                "scripts": {"demo-tool": "demo_package.cli:main"},
                "classifiers": [
                    "Development Status :: 3 - Alpha",
                    "Intended Audience :: Developers",
                    "License :: OSI Approved :: MIT License",
                    PYTHON_3_CLASSIFIER,
                    "Programming Language :: Python :: 3.9",
                    "Programming Language :: Python :: 3.10",
                    "Programming Language :: Python :: 3.11",
                    "Programming Language :: Python :: 3.12",
                    "Programming Language :: Python :: 3.13",
                ],
            },
        },
        "scientific": {
            "build-system": {
                "requires": ["setuptools>=64", "wheel", "numpy"],
                "build-backend": "setuptools.build_meta",
            },
            "project": {
                "name": "scientific-demo",
                "version": "1.2.3",
                "description": "A scientific computing demo package",
                "readme": README_FILE,
                "license": {"text": "BSD-3-Clause"},
                "authors": [{"name": "Scientist", "email": "scientist@example.com"}],
                "requires-python": ">=3.9",
                "dependencies": [
                    "numpy>=1.21.0",
                    "scipy>=1.7.0",
                    "matplotlib>=3.4.0",
                    "pandas>=1.3.0",
                    "scikit-learn>=1.0.0",
                ],
                "optional-dependencies": {
                    "dev": [PYTEST_VERSION, "pytest-cov", "black", "mypy", "ruff"],
                    "docs": ["sphinx", "numpydoc", "sphinx-gallery"],
                    "test": ["pytest", "pytest-benchmark"],
                },
                "urls": {
                    "homepage": "https://github.com/example/scientific-demo",
                    "repository": "https://github.com/example/scientific-demo.git",
                    "documentation": "https://scientific-demo.readthedocs.io",
                    "issues": "https://github.com/example/scientific-demo/issues",
                },
                "classifiers": [
                    "Development Status :: 4 - Beta",
                    "Intended Audience :: Science/Research",
                    "License :: OSI Approved :: BSD License",
                    PYTHON_3_CLASSIFIER,
                    "Topic :: Scientific/Engineering",
                    "Topic :: Scientific/Engineering :: Mathematics",
                ],
            },
        },
        "webapp": {
            "build-system": {
                "requires": ["poetry-core>=1.0.0"],
                "build-backend": "poetry.core.masonry.api",
            },
            "project": {
                "name": "webapp-demo",
                "version": "2.0.0",
                "description": "A web application demo package",
                "readme": README_FILE,
                "license": {"text": "Apache-2.0"},
                "authors": [{"name": "Web Developer", "email": "webdev@example.com"}],
                "requires-python": ">=3.10",
                "dependencies": [
                    "fastapi>=0.68.0",
                    "uvicorn[standard]>=0.15.0",
                    "pydantic>=1.8.0",
                    "sqlalchemy>=1.4.0",
                    "alembic>=1.7.0",
                ],
                "optional-dependencies": {
                    "dev": [PYTEST_VERSION, "pytest-asyncio", "httpx", "black", "mypy"],
                    "production": ["gunicorn", "psycopg2-binary"],
                    "monitoring": ["prometheus-client", "sentry-sdk"],
                },
                "scripts": {
                    "webapp-demo": "webapp_demo.main:app",
                    "webapp-migrate": "webapp_demo.migrate:main",
                },
                "classifiers": [
                    "Development Status :: 5 - Production/Stable",
                    "Framework :: FastAPI",
                    "Intended Audience :: Developers",
                    "License :: OSI Approved :: Apache Software License",
                    PYTHON_3_CLASSIFIER,
                    "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
                ],
            },
        },
    }

    return demos.get(demo_type, demos["simple"])


def generate_recipe_from_data(pyproject_data: dict[str, Any]) -> str:
    """Generate a recipe from pyproject.toml data."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=TOML_SUFFIX, delete=False) as f:
        temp_path = Path(f.name)

    try:
        # Write the TOML data to temporary file
        with open(temp_path, "w") as f:
            toml.dump(pyproject_data, f)

        # Load the TOML data and generate recipe
        toml_data = load_pyproject_toml(temp_path)
        recipe_dict = assemble_recipe(toml_data, temp_path.parent, temp_path.parent)

        # Convert to YAML string
        return yaml.dump(recipe_dict, default_flow_style=False, sort_keys=False)
    finally:
        temp_path.unlink()


def demo_simple_package() -> str:
    """Generate a recipe for a simple package demo."""
    print("� Generating recipe for a simple package...")
    pyproject_data = create_demo_pyproject("simple")
    return generate_recipe_from_data(pyproject_data)


def demo_scientific_package() -> str:
    """Generate a recipe for a scientific computing package demo."""
    print("🔬 Generating recipe for a scientific computing package...")
    pyproject_data = create_demo_pyproject("scientific")
    return generate_recipe_from_data(pyproject_data)


def demo_webapp_package() -> str:
    """Generate a recipe for a web application package demo."""
    print("🌐 Generating recipe for a web application package...")
    pyproject_data = create_demo_pyproject("webapp")
    return generate_recipe_from_data(pyproject_data)


def demo_current_project() -> Optional[str]:
    """Generate a recipe for the current project (pyrattler-recipe-autogen itself)."""
    print("🔄 Generating recipe for pyrattler-recipe-autogen itself...")

    # Look for pyproject.toml in current directory and parent directories
    current_dir = Path.cwd()
    for path in [current_dir] + list(current_dir.parents):
        pyproject_path = path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                toml_data = load_pyproject_toml(pyproject_path)
                recipe_dict = assemble_recipe(
                    toml_data, pyproject_path.parent, pyproject_path.parent
                )
                return yaml.dump(recipe_dict, default_flow_style=False, sort_keys=False)
            except Exception as e:
                print(f"❌ Error generating recipe: {e}")
                return None

    print("❌ No pyproject.toml found in current directory or parent directories")
    return None


def print_demo_header(title: str) -> None:
    """Print a formatted header for demo sections."""
    print("\n" + "=" * 80)
    print(f"🎯 {title}")
    print("=" * 80)


def print_recipe_preview(recipe: str, max_lines: int = 30) -> None:
    """Print a preview of the generated recipe."""
    lines = recipe.split("\n")
    if len(lines) <= max_lines:
        print(recipe)
    else:
        print("\n".join(lines[:max_lines]))
        print(f"\n... (showing first {max_lines} lines of {len(lines)} total)")
        print("💡 Use --full to see the complete recipe")


def run_simple_demo() -> None:
    """Run demos for individual package types."""
    demos = [
        ("Simple Package", demo_simple_package),
        ("Scientific Computing Package", demo_scientific_package),
        ("Web Application Package", demo_webapp_package),
    ]

    for title, demo_func in demos:
        print_demo_header(title)
        try:
            recipe = demo_func()
            print_recipe_preview(recipe)
        except Exception as e:
            print(f"❌ Error running demo: {e}")
        print()


def run_current_demo() -> None:
    """Run demo for current project."""
    print_demo_header("Current Project (pyrattler-recipe-autogen)")
    try:
        recipe = demo_current_project()
        if recipe:
            print_recipe_preview(recipe)
        else:
            print("❌ Failed to generate recipe")
    except Exception as e:
        print(f"❌ Error running demo: {e}")


def run_full_demo(full_output: bool = False) -> None:
    """Run all demos with specified output level."""
    demos_to_run = [
        ("Simple Package", demo_simple_package),
        ("Scientific Computing Package", demo_scientific_package),
        ("Web Application Package", demo_webapp_package),
        ("Current Project (pyrattler-recipe-autogen)", demo_current_project),
    ]

    for title, demo_func in demos_to_run:
        print_demo_header(title)

        try:
            recipe = demo_func()
            if recipe:
                if full_output:
                    print(recipe)
                else:
                    print_recipe_preview(recipe)
            else:
                print("❌ Failed to generate recipe")
        except Exception as e:
            print(f"❌ Error running demo: {e}")

        print()  # Add spacing between demos


def run_demo(demo_type: str = "all", full_output: bool = False) -> None:
    """
    Run the demonstration with different package types.

    Args:
        demo_type: Type of demo to run ('all', 'simple', 'scientific', 'webapp', 'current')
        full_output: If True, show complete recipes instead of previews
    """

    print(
        textwrap.dedent("""
    🎉 Welcome to pyrattler-recipe-autogen Demo!

    This demo will show you how pyrattler-recipe-autogen generates
    conda-forge recipe.yaml files from different types of Python projects.
    """).strip()
    )

    if demo_type == "all":
        run_full_demo(full_output)
    elif demo_type in ["simple", "scientific", "webapp"]:
        run_simple_demo()
    elif demo_type == "current":
        run_current_demo()
    else:
        print(f"❌ Unknown demo type: {demo_type}")
        print("Available types: all, simple, scientific, webapp, current")
        return

    print(
        textwrap.dedent("""
    ✨ Demo complete!

    To try pyrattler-recipe-autogen with your own project:
    1. Navigate to your Python project directory
    2. Run: pyrattler-recipe-autogen
    3. Check the generated recipe.yaml file

    For more options: pyrattler-recipe-autogen --help
    """).strip()
    )


def main() -> None:
    """Main entry point for the demo module."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Demo pyrattler-recipe-autogen functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python -m pyrattler_recipe_autogen.demo                    # Run all demos
          python -m pyrattler_recipe_autogen.demo --type simple      # Simple package demo
          python -m pyrattler_recipe_autogen.demo --type current     # Current project demo
          python -m pyrattler_recipe_autogen.demo --full             # Show full recipes
        """),
    )

    parser.add_argument(
        "--type",
        choices=["all", "simple", "scientific", "webapp", "current"],
        default="all",
        help="Type of demo to run (default: all)",
    )

    parser.add_argument(
        "--full", action="store_true", help="Show complete recipes instead of previews"
    )

    args = parser.parse_args()

    run_demo(demo_type=args.type, full_output=args.full)


if __name__ == "__main__":
    main()
