"""
Command line interface for pyrattler-recipe-autogen.
"""

import argparse
import pathlib
import sys
from collections.abc import Sequence
from typing import Optional

from .core import generate_recipe


def main(argv: Optional[Sequence[str]] = None) -> None:
    """
    Main CLI entry point for generating Rattler-Build recipes.

    Args:
        argv: Command line arguments (defaults to sys.argv)
    """
    ap = argparse.ArgumentParser(
        description="Generate Rattler-Build recipe.yaml from pyproject.toml"
    )
    ap.add_argument(
        "-i",
        "--input",
        default="pyproject.toml",
        help="pyproject.toml path (default: ./pyproject.toml)",
    )
    ap.add_argument(
        "-o",
        "--output",
        default="recipe/recipe.yaml",
        help="Output recipe.yaml path (default: ./recipe/recipe.yaml)",
    )
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output file if it exists (default: backup existing file).",
    )
    args = ap.parse_args(argv)

    pyproject_path = pathlib.Path(args.input).expanduser()
    output_path = pathlib.Path(args.output).expanduser()

    try:
        generate_recipe(pyproject_path, output_path, args.overwrite)
    except FileNotFoundError as e:
        sys.exit(str(e))
    except Exception as e:
        sys.exit(f"Error generating recipe: {e}")


if __name__ == "__main__":
    main()
