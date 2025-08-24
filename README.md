# pyrattler-recipe-autogen

Automatically generates recipe.yaml files for rattler-build directly from your Python project's pyproject.toml, eliminating the need for manual recipe creation.
Features intelligent auto-detection, advanced dependency management, and comprehensive integration support.

<!-- Badges -->

[![CI](https://github.com/millsks/pyrattler-recipe-autogen/workflows/CI/badge.svg)](https://github.com/millsks/pyrattler-recipe-autogen/actions/workflows/ci.yml)
[![Test Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen)](https://github.com/millsks/pyrattler-recipe-autogen)
[![PyPI version](https://img.shields.io/pypi/v/pyrattler-recipe-autogen?color=blue)](https://pypi.org/project/pyrattler-recipe-autogen/)
[![Python Version](https://img.shields.io/badge/python-3.9%E2%80%933.13-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Pixi Badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/prefix-dev/pixi/main/assets/badge/v0.json)](https://pixi.sh)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## ✨ Features

### 🚀 Core Functionality

- **Automatic Recipe Generation**: Creates complete recipe.yaml files from pyproject.toml
- **Dynamic Version Resolution**: Supports setuptools_scm, hatch-vcs, and other dynamic versioning
- **Intelligent Source Detection**: Auto-detects PyPI, Git repositories, and local sources
- **Smart Dependency Mapping**: Converts Python dependencies to conda equivalents

### 🔧 Advanced Build Configuration

- **Multi-Backend Support**: Works with hatchling, setuptools, flit, poetry backends
- **Entry Point Detection**: Automatically configures console scripts and GUI applications
- **Platform-Specific Builds**: Handles conditional dependencies and platform variants
- **Custom Build Scripts**: Detects and configures custom build processes

### 🧪 Intelligent Testing

- **Test Auto-Detection**: Finds pytest, unittest, and custom test configurations
- **Import Testing**: Generates appropriate import tests for your package
- **Test Dependency Management**: Separates test requirements from runtime dependencies
- **Coverage Integration**: Supports pytest-cov and coverage.py configurations

### 🌍 Platform & Environment Support

- **Cross-Platform Builds**: Supports Linux, macOS, Windows, and other platforms
- **Architecture Detection**: Handles x86_64, ARM64, and other architectures
- **Python Version Matrix**: Supports multiple Python version requirements
- **Conditional Dependencies**: Platform-specific and environment-specific packages

### 📊 Advanced Context Variables

- **Package Intelligence**: Auto-detects package structure and metadata
- **Build System Analysis**: Identifies build backend and configuration
- **Dependency Categorization**: Classifies runtime, development, and optional dependencies
- **Development Environment**: Detects CI/CD, documentation, and tooling setup

### 🎨 Output Customization

- **Multiple Formats**: Generate YAML or JSON output
- **Template Customization**: Custom templates for different recipe sections
- **Section Control**: Include/exclude specific recipe sections
- **Validation Framework**: Built-in recipe validation and best practice checks
- **Formatting Options**: Configurable indentation, sorting, and style

### 🔗 Integration Enhancements

- **Pixi Integration**: Deep integration with pixi environment management
- **CI/CD Detection**: Supports GitHub Actions, GitLab CI, Travis CI, and more
- **Pre-commit Hooks**: Integration with pre-commit configuration
- **Development Workflow**: Optimization suggestions for development setup
- **Tool Detection**: Identifies pytest, mypy, ruff, and other development tools

### 🔒 Security & Quality Assurance

- **Security Scanning**: Bandit code security analysis and Safety dependency vulnerability checks
- **Code Quality**: Comprehensive linting with Ruff and type checking with MyPy
- **Test Coverage**: High test coverage requirements with pytest and coverage reporting
- **Pre-commit Hooks**: Automated quality checks on every commit

## 📋 Requirements

- Python 3.9 or later
- PyYAML for YAML processing
- PyYAML for YAML processing
- tomli for TOML parsing (Python < 3.11)

## 🚀 Installation

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

### Using Pixi (Recommended)

```bash
git clone https://github.com/millsks/pyrattler-recipe-autogen.git
cd pyrattler-recipe-autogen
pixi install
pixi shell
```

## 📖 Usage

### Command Line Interface

Basic usage:

```bash
# Generate recipe.yaml from pyproject.toml in current directory
pyrattler-recipe-autogen

# Specify input and output files
pyrattler-recipe-autogen -i path/to/pyproject.toml -o path/to/recipe.yaml

# Overwrite existing recipe file
pyrattler-recipe-autogen --overwrite
```

### 🎮 Try the Demo

**Want to see what pyrattler-recipe-autogen can do?** Try the interactive demo:

```bash
# Run all demos (shows simple, scientific, webapp, and current project)
python -m pyrattler_recipe_autogen.demo

# Try specific package types
python -m pyrattler_recipe_autogen.demo --type simple
python -m pyrattler_recipe_autogen.demo --type scientific
python -m pyrattler_recipe_autogen.demo --type webapp

# Analyze the current project
python -m pyrattler_recipe_autogen.demo --type current

# See complete recipes (instead of previews)
python -m pyrattler_recipe_autogen.demo --full
```

**With pixi** (if you have the source):

```bash
pixi run demo          # All demos
pixi run demo-simple   # Simple package demo
pixi run demo-current  # Current project demo
pixi run demo-full     # Full output
```

The demo shows how the tool works with:

- 🔧 **Simple packages**: Basic Python projects with standard dependencies
- 🔬 **Scientific packages**: NumPy/SciPy/matplotlib-based projects
- 🌐 **Web applications**: FastAPI/Django-style projects
- 📦 **Real projects**: Analysis of actual pyproject.toml files

### Programmatic API

Basic recipe generation:

```python
from pathlib import Path
from pyrattler_recipe_autogen import generate_recipe

# Generate recipe from pyproject.toml
generate_recipe(
    pyproject_path=Path("pyproject.toml"),
    output_path=Path("recipe.yaml"),
    overwrite=True
)
```

Advanced configuration with custom output:

```python
from pyrattler_recipe_autogen.core import (
    generate_recipe_with_config,
    OutputConfig,
    IntegrationConfig,
    _detect_integration_enhancements
)

# Configure output options
output_config = OutputConfig(
    output_format="json",           # "yaml" or "json"
    yaml_style="block",            # "default", "block", or "flow"
    include_comments=True,         # Include helpful comments
    sort_keys=True,               # Sort dictionary keys
    indent=4,                     # Indentation level
    exclude_sections=["test"],    # Skip test section
    validate_output=True          # Validate generated recipe
)

# Generate with custom configuration
generate_recipe_with_config(
    pyproject_path=Path("pyproject.toml"),
    output_path=Path("recipe.yaml"),
    config=output_config
)
```

Integration analysis:

```python
from pyrattler_recipe_autogen.core import (
    _detect_integration_enhancements,
    _load_integration_config,
    load_pyproject_toml
)

# Analyze project integrations
toml_data = load_pyproject_toml(Path("pyproject.toml"))
integration_config = _load_integration_config(toml_data)
integration_info = _detect_integration_enhancements(
    Path("."), toml_data, integration_config
)

# Access detected information
print(f"Pixi detected: {integration_info.pixi_detected}")
print(f"CI/CD systems: {integration_info.ci_cd_systems}")
print(f"Development tools: {integration_info.dev_tools}")
print(f"Suggestions: {integration_info.workflow_suggestions}")
```

## ⚙️ Configuration

### Basic Configuration in pyproject.toml

You can customize recipe generation by adding configuration to your `pyproject.toml`:

```toml
[tool.conda.recipe]
# Basic recipe metadata
name = "my-package"
version = "1.0.0"

# Source configuration
[tool.conda.recipe.source]
url = "https://github.com/user/repo/archive/v{{ version }}.tar.gz"
sha256 = "abc123..."

# Build configuration
[tool.conda.recipe.build]
script = "python -m pip install . -vv --no-build-isolation"
number = 0
skip = ["py<39"]

# Requirements
[tool.conda.recipe.requirements]
build = ["pip", "setuptools", "wheel"]
host = ["python", "pip"]
run = ["python", "numpy", "pandas"]

# Test configuration
[tool.conda.recipe.test]
imports = ["my_package"]
commands = ["my-package --help"]
requires = ["pytest"]

# About section
[tool.conda.recipe.about]
summary = "A fantastic Python package"
license = "MIT"
license_file = "LICENSE"
homepage = "https://github.com/user/repo"
```

### Advanced Output Configuration

```toml
[tool.conda.recipe.output]
format = "yaml"              # "yaml" or "json"
yaml_style = "block"         # "default", "block", or "flow"
include_comments = true      # Add helpful comments
sort_keys = false           # Sort dictionary keys
indent = 2                  # Indentation level
validate_output = true      # Validate generated recipe
include_sections = []       # Only include these sections (empty = all)
exclude_sections = ["test"] # Exclude these sections
json_indent = 2            # JSON indentation level

# Custom templates for specific sections
[tool.conda.recipe.output.custom_templates]
package = "Custom package template"
```

### Integration Enhancement Configuration

```toml
[tool.conda.recipe.integration]
pixi_integration = true          # Detect pixi configuration
ci_cd_detection = true          # Detect CI/CD systems
precommit_integration = true    # Detect pre-commit setup
dev_workflow_optimization = true # Analyze development workflow
suggest_improvements = true     # Generate improvement suggestions
```

### Context Variables and Platform Support

```toml
[tool.conda.recipe.context]
# Define custom context variables
python_min = "3.9"
package_name = "my-package"

# Platform-specific configurations
[tool.conda.recipe.platforms]
linux = ["linux-64", "linux-aarch64"]
macos = ["osx-64", "osx-arm64"]
windows = ["win-64"]

# Architecture-specific dependencies
[tool.conda.recipe.requirements.run.linux]
additional = ["linux-specific-package"]

[tool.conda.recipe.requirements.run.macos]
additional = ["macos-specific-package"]
```

## 🏗️ Generated Recipe Structure

The tool generates comprehensive recipe.yaml files with the following sections:

```yaml
context:
  name: my-package
  version: 1.0.0
  python_min: "3.9"
  # ... additional context variables

package:
  name: ${{ name }}
  version: ${{ version }}

source:
  url: https://pypi.org/packages/source/m/my-package/my_package-1.0.0.tar.gz
  # or git repository, local path, etc.

build:
  script: python -m pip install . -vv --no-build-isolation
  number: 0
  # ... build configuration

requirements:
  build: []
  host: [python, pip]
  run: [python, numpy, pandas]

test:
  python:
    imports: [my_package]
  commands: [my-package --help]

about:
  summary: A fantastic Python package
  license: MIT
  license_file: LICENSE
  homepage: https://github.com/user/repo
```

## 🔧 Advanced Features

### Dynamic Version Resolution

Supports multiple dynamic versioning systems:

- **setuptools_scm**: Git tag-based versioning
- **hatch-vcs**: Modern Git versioning for hatch
- **poetry**: Poetry dynamic versioning
- **setuptools**: Simple dynamic versions

### Smart Dependency Mapping

- Converts Python package names to conda equivalents
- Handles version constraints and markers
- Separates runtime, build, and test dependencies
- Manages optional and extra dependencies

### Platform-Specific Builds

- Detects platform-specific dependencies
- Configures appropriate selectors
- Handles architecture requirements
- Manages Python version matrices

### Integration Analysis

- **Pixi Detection**: Analyzes pixi.toml and environments
- **CI/CD Systems**: Detects GitHub Actions, GitLab CI, Travis CI, etc.
- **Development Tools**: Finds pytest, mypy, ruff, black, and more
- **Pre-commit**: Analyzes .pre-commit-config.yaml
- **Workflow Suggestions**: Recommends improvements and best practices

- **Workflow Suggestions**: Recommends improvements and best practices

## 📚 Examples

### Simple Python Package

For a basic Python package with the following `pyproject.toml`:

```toml
[project]
name = "my-simple-package"
version = "1.0.0"
description = "A simple Python package"
dependencies = ["requests", "click"]
requires-python = ">=3.9"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Generated recipe:

```yaml
context:
  name: my-simple-package
  version: 1.0.0
  python_min: "3.9"

package:
  name: ${{ name }}
  version: ${{ version }}

source:
  url: https://pypi.org/packages/source/m/my-simple-package/my_simple_package-1.0.0.tar.gz

build:
  script: python -m pip install . -vv --no-build-isolation
  number: 0

requirements:
  host: [python, pip]
  run: [python, requests, click]

test:
  python:
    imports: [my_simple_package]
```

### Complex Package with Pixi

For a project using pixi with the following structure:

```toml
# pyproject.toml
[project]
name = "advanced-package"
dynamic = ["version"]
dependencies = ["numpy>=1.20", "pandas>=1.3"]
optional-dependencies.dev = ["pytest", "mypy", "ruff"]

[tool.hatch.version]
source = "vcs"

# pixi.toml
[project]
name = "advanced-package"
channels = ["conda-forge", "bioconda"]
platforms = ["linux-64", "osx-64", "osx-arm64"]

[dependencies]
python = ">=3.9"
numpy = ">=1.20"
pandas = ">=1.3"

[feature.dev.dependencies]
pytest = "*"
mypy = "*"
ruff = "*"
```

Generated recipe includes pixi-aware dependency management and development tool detection.

## 🚨 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'tomllib'`  
**Solution**: Install tomli for Python < 3.11: `pip install tomli`

**Issue**: Recipe generation fails with "No version found"  
**Solution**: Ensure version is specified in `[project]` or configure dynamic versioning properly

**Issue**: Dependencies not mapping correctly  
**Solution**: Check for conda-forge equivalents or specify custom mappings in `[tool.conda.recipe.requirements]`

**Issue**: Build script not detected  
**Solution**: Specify custom build script in `[tool.conda.recipe.build]`

### Debug Mode

Enable verbose logging to debug issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from pyrattler_recipe_autogen import generate_recipe
# Your code here
```

### Validation Errors

The tool includes built-in validation. Common validation warnings:

- **Missing recommended sections**: Add missing package, source, or requirements sections
- **Package version missing**: Ensure version is specified or dynamic versioning is configured
- **Undefined context variables**: Check template variables in your configuration
- **Unused context variables**: Remove unused variables from context section

## 🧪 Development

### Setup Development Environment

Using pixi (recommended):

```bash
git clone https://github.com/millsks/pyrattler-recipe-autogen.git
cd pyrattler-recipe-autogen
pixi install
pixi shell
```

Using pip:

```bash
git clone https://github.com/millsks/pyrattler-recipe-autogen.git
cd pyrattler-recipe-autogen
pip install -e ".[dev]"
```

### Development Commands

```bash
# Run tests
pixi run test

# Run tests with coverage
pixi run test-cov

# Format code
pixi run format

# Run linting
pixi run lint

# Run type checking
pixi run type-check

# Run security checks
pixi run security-check

# Run all checks (lint + type-check)
pixi run check

# Run all checks including security (lint + type-check + security-check)
pixi run check-all

# Build package
pixi run build

# Clean build artifacts
pixi run clean

# Check current version
pixi run version
```

### Running the Full CI Pipeline

```bash
pixi run ci  # Runs format + check + test-cov (includes security checks)
```

### Project Structure

```
pyrattler-recipe-autogen/
├── src/
│   └── pyrattler_recipe_autogen/
│       ├── __init__.py
│       ├── _version.py          # Auto-generated
│       ├── cli.py              # Command-line interface
│       └── core.py             # Core recipe generation logic
├── tests/
│   ├── test_cli.py            # CLI tests
│   ├── test_core.py           # Core functionality tests
│   └── test_init.py           # Package initialization tests
├── pyproject.toml             # Project configuration
├── pixi.toml                 # Pixi environment configuration
├── README.md                 # This file
└── LICENSE                   # MIT license
```

## 🔄 Versioning

This project uses [hatch-vcs](https://github.com/ofek/hatch-vcs) for automatic version management:

- **Tagged releases**: Use the tag version (e.g., `v0.1.0` → `0.1.0`)
- **Development builds**: Include commit info (e.g., `0.1.0.dev5+g1234567`)
- **Dirty working directories**: Append `.dirty` to version

Check current version: `pixi run version`

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### 📚 Documentation

- **[Release Process](RELEASE_PROCESS.md)**: Complete guide for creating and publishing releases
- **[Contributing Guidelines](CONTRIBUTING.md)**: Development setup and contribution workflow
- **[Security Policy](SECURITY.md)**: How to report security vulnerabilities
- **[Changelog](CHANGELOG.md)**: Release history and version changes

### Quick Start for Contributors

1. **Fork and Clone**:

   ```bash
   git clone https://github.com/yourusername/pyrattler-recipe-autogen.git
   cd pyrattler-recipe-autogen
   ```

2. **Setup Development Environment**:

   ```bash
   pixi install
   pixi run dev-setup  # Installs pre-commit hooks
   ```

3. **Create a Branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Changes** and ensure tests pass:

   ```bash
   pixi run format       # Format code
   pixi run check-all    # Run linting, type checking, and security checks
   pixi run test-cov     # Run tests with coverage
   ```

5. **Commit with Conventional Commits**:

   ```bash
   git commit -m "feat: add new feature"
   # or
   git commit -m "fix: resolve issue with dependency mapping"
   ```

6. **Push and Create PR**:

   ```bash
   git push origin feature/your-feature-name
   ```

### Code Quality Standards

- **Test Coverage**: Maintain >95% test coverage
- **Type Hints**: All functions must have proper type annotations
- **Documentation**: Add docstrings for all public functions and classes
- **Conventional Commits**: Use conventional commit format for all commits
- **Pre-commit Hooks**: All hooks must pass before committing

### Development Workflow

1. **Setup**: Use `pixi install` and `pixi run dev-setup`
2. **Development**: Use `pixi run` commands for all tasks
3. **Testing**: Write tests for new features in `tests/`
4. **Documentation**: Update README and docstrings
5. **Quality**: Ensure all pre-commit hooks pass
6. **Pull Request**: Create PR with clear description

## 📊 Project Statistics

- **Test Coverage**: 97% (core.py), 95% (overall)
- **Code Quality**: Pre-commit hooks with ruff, mypy, bandit
- **Documentation**: Comprehensive docstrings and examples
- **CI/CD**: GitHub Actions with automated testing and quality checks
- **Dependencies**: Minimal runtime dependencies for reliability

## 🗺️ Roadmap

### Completed Features ✅

- ✅ **Enhanced Build Configuration**: Multi-backend support and intelligent detection
- ✅ **Advanced Requirements Management**: Smart dependency mapping and pixi integration
- ✅ **Test Section Intelligence**: Auto-detection and configuration
- ✅ **Platform/Variant Support**: Cross-platform builds and architecture handling
- ✅ **Advanced Context Variables**: Package intelligence and environment detection
- ✅ **Output Customization**: Multiple formats and validation framework
- ✅ **Integration Enhancements**: CI/CD, pixi, and development tool detection
- ✅ **Documentation Enhancement**: Comprehensive docs and examples

### Future Enhancements 🚀

- 🔄 **GUI Interface**: Desktop application for recipe generation
- 🔄 **Recipe Templates**: Pre-built templates for common package types
- 🔄 **Batch Processing**: Generate recipes for multiple packages
- 🔄 **Cloud Integration**: Direct integration with conda-forge/feedstocks
- 🔄 **Package Analysis**: Deep dependency analysis and optimization suggestions

## 🐛 Known Issues

- Windows path handling in some edge cases
- Large dependency trees may cause slow generation
- Some proprietary build systems not fully supported

See [Issues](https://github.com/millsks/pyrattler-recipe-autogen/issues) for current bug reports and feature requests.

## 📖 API Documentation

Full API documentation is available in the source code docstrings. Key classes and functions:

### Core Functions

- `generate_recipe()`: Main recipe generation function
- `generate_recipe_with_config()`: Advanced generation with custom configuration
- `load_pyproject_toml()`: Load and parse pyproject.toml files

### Configuration Classes

- `OutputConfig`: Configure output format and validation
- `IntegrationConfig`: Configure integration detection
- `IntegrationInfo`: Results of integration analysis

### Detection Functions

- `_detect_pixi_integration()`: Analyze pixi configuration
- `_detect_ci_cd_systems()`: Find CI/CD systems
- `_detect_dev_tools()`: Identify development tools

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Rattler](https://github.com/mamba-org/rattler) - Fast conda package management
- [Pixi](https://pixi.sh) - Modern Python package management
- [conda-forge](https://conda-forge.org) - Community-driven conda package repository
- [PyPA](https://www.pypa.io) - Python Packaging Authority standards

## 📞 Support

- **Documentation**: Check this README and source code docstrings
- **Issues**: Report bugs on [GitHub Issues](https://github.com/millsks/pyrattler-recipe-autogen/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/millsks/pyrattler-recipe-autogen/discussions)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines

---

## Happy Recipe Generating! 🚀

## Development

### Prerequisites

- [Pixi](https://prefix.dev/docs/pixi/overview) - Modern package management for Python

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/millsks/pyrattler-recipe-autogen.git
cd pyrattler-recipe-autogen

# Install dependencies (includes editable install of the project)
pixi install

# Set up development environment (install pre-commit hooks)
pixi run dev-setup
```

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to ensure code quality and consistency. The hooks run automatically on every commit and include:

- **Code Formatting**: Ruff formatting and linting
- **Type Checking**: MyPy static type analysis
- **Security Scanning**: Bandit security linter
- **File Validation**: YAML, TOML, JSON syntax checking
- **Git Best Practices**: Large file detection, merge conflict detection
- **Commit Messages**: Conventional commit format validation
- **Documentation**: Markdown linting and formatting
- **GitHub Actions**: Workflow file validation

```bash
# Install hooks (done automatically by dev-setup)
pixi run pre-commit-install

# Run all hooks manually
pixi run pre-commit-run

# Run specific hook
pixi run pre-commit run ruff --all-files
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
pixi run type-check

# Run security checks
pixi run security-check

# Run all checks (lint + type-check)
pixi run check

# Run all checks including security (lint + type-check + security-check)
pixi run check-all

# Build package
pixi run build

# Clean build artifacts
pixi run clean

# Check current version
pixi run version

# Run the full CI pipeline (format + check + test-cov)
pixi run ci

# Generate changelog
pixi run changelog

# Preview unreleased changes
pixi run changelog-unreleased

# Preview latest version changes
pixi run changelog-latest

# Preview what the next release would look like
pixi run release-preview
```

### Changelog Generation

This project uses [git-cliff](https://git-cliff.org/) to automatically generate changelogs based on conventional commits:

```bash
# Generate complete changelog
pixi run changelog

# See unreleased changes
pixi run changelog-unreleased

# Preview the next release
pixi run release-preview
```

The changelog follows [Keep a Changelog](https://keepachangelog.com/) format and uses [Conventional Commits](https://www.conventionalcommits.org/) for automated categorization.

````

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
````

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

## Releases and Contributing

### Versioning and Releases

This project uses `hatch-vcs` for automatic version management based on git tags:

- **Development versions**: Generated automatically as `0.1.devN` (where N is the number of commits since the last tag)
- **Release versions**: Created by pushing git tags in the format `v1.0.0`

#### Creating a Release

**For maintainers**: Use the streamlined release workflow in GitHub Actions.

1. **Go to Actions** → "Release and Publish" workflow
2. **Click "Run workflow"** and fill in the form:
   - Version (e.g., `1.0.0`)
   - Pre-release checkbox (for alpha/beta)
   - Publishing options (PyPI, Test PyPI)
3. **Wait for completion** - everything is automated!

**For complete details**: See [RELEASE_PROCESS.md](RELEASE_PROCESS.md)

#### Test Publishing

The release workflow includes optional Test PyPI publishing for verification before production release.

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pixi run test`
5. Run checks: `pixi run check`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
