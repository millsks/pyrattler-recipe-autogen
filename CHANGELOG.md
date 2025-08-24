# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.8] - 2025-08-24

### 🐛 Bug Fixes

- Add missing v0.9.8 to CHANGELOG.md and improve git-cliff config

## [0.9.7] - 2025-08-24

### ⚙️ Miscellaneous Tasks

- Extract release notes from CHANGELOG.md for GitHub releases

### 📚 Documentation

- Add comprehensive badges to README.md

## [0.9.6] - 2025-08-24

### 📚 Documentation

- Remove public security vulnerability template
- Improve issue and PR guidance in CONTRIBUTING.md

## [0.9.5] - 2025-08-24

### 🐛 Bug Fixes

- Ensure git-cliff sees the release tag when generating changelog

## [0.9.2] - 2025-08-24

### 🐛 Bug Fixes

- Correct release notes formatting in GitHub releases

### 📚 Documentation

- Regenerate CHANGELOG.md using git-cliff with full project history

## [0.9.1] - 2025-08-24

### Build

- **deps**: Update all pre-commit hook versions to latest

### ⚙️ Miscellaneous Tasks

- **deps**: Bump actions/checkout from 4 to 5 (#4)
- **deps**: Bump prefix-dev/setup-pixi from 0.8.1 to 0.9.0 (#5)

### ⭐ Features

- Enhance build configuration with auto-detection
- Advanced Requirements Management with conditional dependencies
- Test Section Enhancement with intelligent auto-detection
- Source Section Intelligence with auto-detection
- Add platform/variant support with intelligent auto-detection
- Implement Output Customization enhancement
- Implement Integration Enhancements
- Add comprehensive security reporting infrastructure
- Add Copilot instructions for pull request reviews
- Consolidate release and publishing workflows
- Add comprehensive repository maintenance workflows
- Add automated labeling system
- Add Python 3.13 support
- Update package version to 0.1.3.dev25 and sha256 checksum
- Add comprehensive interactive demo module
- Standardize task naming and add comprehensive security scanning
- Use Personal Access Token for release workflow to bypass branch protection
- Add PyPI publishing steps to release workflow

### 🐛 Bug Fixes

- Exclude auto-generated _version.py from linting and coverage
- Resolve markdown linting issues in documentation
- Enable automatic dependabot scans
- Update CI workflow to use standardized type-check task name
- Update changelog generation to use specific tag version

### 📚 Documentation

- Add comprehensive release process documentation
- Update README with documentation references and release process

### 🚜 Refactor

- Consolidate bandit configuration in pyproject.toml

## [0.1.2] - 2025-08-18

### 🐛 Bug Fixes

- Add contents:write permission for uploading release assets

## [0.1.1] - 2025-08-18

### 🐛 Bug Fixes

- Simplify version verification in publish workflow to handle editable installs

## [0.1.0] - 2025-08-18

### ⚙️ Miscellaneous Tasks

- Update pixi tasks for pre-commit integration
- Add security report files to gitignore
- Update package version in pixi.lock

### ⭐ Features

- Add pyrattler-recipe-autogen package for generating Rattler-Build recipes
- Add type stubs for PyYAML and update import handling for tomli
- Add pre-commit configuration and hooks for code quality

### 🎨 Styling

- Clean up code formatting and improve readability across multiple files
- Improve YAML formatting in GitHub Actions workflows

### 🐛 Bug Fixes

- Update CI workflow to trigger on main and develop branches
- Remove obsolete rattler-build package references from pixi.lock
- Add type cast for setuptools_scm version resolution
- Simplify type casting for setuptools_scm version resolution
- Improve cross-platform compatibility for temporary file handling in tests
- Simplify command for package integrity check in CI workflows
- Simplify safety and bandit command execution in CI workflow
- Remove safety check from CI workflow
- Update Pixi setup to version 0.9.0 and adjust pixi-version to 0.52.0
- Streamline imports and enhance cross-platform compatibility in test_core.py
- Update SonarQube project key for consistency
- Update SonarQube project key for accuracy
- Update SonarCloud configuration for project key and exclusions
- Update SonarCloud Quality Gate action version to v1.2.0
- Remove comment from SonarCloud organization key for clarity
- Normalize path handling for cross-platform compatibility in tests
- Enhance dynamic version resolution with setuptools_scm handling and tests
- Update dynamic version resolution fallback to use placeholder for unknown backends
- Improve handling of Windows cross-drive paths in _get_relative_path function
- Update version in pixi.lock and refactor setuptools_scm import handling in core.py and tests
- Update Pixi setup to version 0.9.0 and adjust Pixi version to 0.52.0
- Configure hatch-vcs to avoid local version identifiers for PyPI uploads

### 📚 Documentation

- Improve changelog formatting and organization
- Enhance README with pre-commit hooks documentation

### 🧪 Testing

- Add unit tests for CLI functionality and package initialization

<!-- generated by git-cliff -->
