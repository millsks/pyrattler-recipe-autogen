# pyrattler-recipe-autogen

Automatically generates recipe.yaml files for rattler-build directly from your Python project's pyproject.toml, eliminating the need for manual recipe creation.

## Installation

### Requirements
- Python 3.9 or later

### From PyPI (when published)
```bash
pip install pyrattler-recipe-autogen
```

### From Source
```bash
git clone https://github.com/millsks/pyrattler-recipe-autogen.git
cd pyrattler-recipe-autogen
pip install -e .
```

## Usage

### Command Line Interface

After installation, you can use the `pyrattler-recipe-autogen` command:

```bash
# Generate recipe.yaml from pyproject.toml in current directory
pyrattler-recipe-autogen

# Specify input and output files
pyrattler-recipe-autogen -i path/to/pyproject.toml -o path/to/recipe.yaml

# Overwrite existing recipe file
pyrattler-recipe-autogen --overwrite
```

### Programmatic Usage

You can also use the package programmatically:

```python
from pathlib import Path
from pyrattler_recipe_autogen import generate_recipe

# Generate recipe from pyproject.toml
generate_recipe(
    pyproject_path=Path("pyproject.toml"),
    output_path=Path("recipe.yaml"),
    overwrite=False
)
```

## Features

• **Automatic Project Data Extraction**: Pulls canonical project data from `[project]` section
• **Dynamic Version Resolution**: Handles dynamic version resolution from build backends (setuptools_scm, hatchling, poetry)
• **Pixi Integration**: Uses Pixi tables for requirement mapping when `[tool.pixi]` is present
• **Flexible Configuration**: Reads extra/override keys from `[tool.conda.recipe.*]` sections
• **License Detection**: Automatically detects license types from license files
• **Python Version Handling**: Extracts Python version constraints from `requires-python`

## Versioning

This project uses [hatch-vcs](https://github.com/ofek/hatch-vcs) for automatic version management based on Git tags. The version is dynamically determined from Git tags and commits:

- Tagged releases use the tag version (e.g., `v0.1.0` → `0.1.0`)
- Development builds include commit information (e.g., `0.1.0.dev5+g1234567`)
- Dirty working directories append `.dirty` to the version

To check the current version:
```bash
pixi run version
```

## Development

### Prerequisites
- [Pixi](https://prefix.dev/docs/pixi/overview) - Modern package management for Python

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/millsks/pyrattler-recipe-autogen.git
cd pyrattler-recipe-autogen

# Install dependencies (includes editable install of the project)
pixi install

# Set up development environment (install pre-commit hooks)
pixi run dev-setup
```

### Development Tasks

Pixi provides convenient commands for development tasks:

```bash
# The project is automatically installed in editable mode when you run pixi install

# Run tests
pixi run test

# Run tests with coverage
pixi run test-cov

# Format code with ruff
pixi run format

# Run linting
pixi run lint

# Run type checking
pixi run typecheck

# Run all checks (lint + typecheck)
pixi run check

# Build package
pixi run build

# Clean build artifacts
pixi run clean

# Check current version
pixi run version

# Run the full CI pipeline (format + check + test-cov)
pixi run ci
```

### Using Different Environments

Pixi supports multiple environments for different purposes:

```bash
# Use the default development environment
pixi shell

# Use the test-only environment
pixi shell -e test

# Use the lint-only environment  
pixi shell -e lint

# Run tasks in specific environments
pixi run -e test test
pixi run -e lint lint
```

### Package Structure

The project follows a src layout:

```
pyrattler-recipe-autogen/
├── src/
│   └── pyrattler_recipe_autogen/
│       ├── __init__.py          # Package initialization and exports
│       ├── core.py              # Core business logic
│       └── cli.py               # Command line interface
├── tests/                       # Test suite
├── pyproject.toml              # Package configuration
├── generate_conda_recipe.py    # Legacy wrapper script
└── dev.py                      # Development utility script
```

## Configuration

The tool reads configuration from your `pyproject.toml` file and supports additional conda-specific configuration under `[tool.conda.recipe.*]` sections:

```toml
[tool.conda.recipe.extra_context]
# Additional context variables

[tool.conda.recipe.about]
# Override about section fields

[tool.conda.recipe.build]
# Override build configuration

[tool.conda.recipe.source]
# Override source configuration

[tool.conda.recipe.test]
# Test configuration

[tool.conda.recipe.extra]
# Extra recipe sections
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
