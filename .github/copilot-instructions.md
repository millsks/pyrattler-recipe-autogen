# Copilot Instructions for Pull Request Reviews

This file provides guidance for GitHub Copilot when reviewing pull requests for the pyrattler-recipe-autogen project.

## Project Overview

**pyrattler-recipe-autogen** is a Python package that automatically generates conda-forge recipe
files from Python project metadata. It uses pixi for dependency management and follows modern Python
packaging standards.

### Key Technologies

- **Python 3.9+** with type hints and modern syntax
- **Pixi** for cross-platform environment management
- **Hatchling** build backend with hatch-vcs for versioning
- **Ruff** for linting and formatting
- **MyPy** for strict type checking
- **Pytest** with coverage for testing
- **Pre-commit hooks** for code quality

## Code Review Priorities

### 1. **Type Safety & Code Quality** (HIGH PRIORITY)

- Ensure all functions have proper type hints
- Check for mypy compliance - no `Any` types unless absolutely necessary
- Verify proper error handling with specific exception types
- Look for missing docstrings on public functions/classes

### 2. **Testing Coverage** (HIGH PRIORITY)

- New features must include comprehensive tests
- Edge cases should be covered (empty inputs, invalid data, etc.)
- Test functions should follow the pattern: `test_<function_name>_<scenario>`
- Mock external dependencies appropriately

### 3. **Recipe Generation Logic** (CRITICAL)

Focus on the core functionality in `src/pyrattler_recipe_autogen/core.py`:

- Validate conda-forge recipe YAML structure
- Check dependency parsing and transformation
- Ensure platform-specific handling (Windows, macOS, Linux)
- Verify URL validation and source handling

### 4. **Performance & Efficiency**

- Flag inefficient loops or redundant operations
- Check for proper resource cleanup (file handles, etc.)
- Ensure lazy loading where appropriate
- Watch for memory usage in file processing

## Coding Standards

### Python Style

```python
# Good: Clear, typed function with docstring
def parse_requirements(file_path: Path) -> list[str]:
    """Parse requirements from a requirements file.

    Args:
        file_path: Path to the requirements file

    Returns:
        List of requirement strings

    Raises:
        FileNotFoundError: If the requirements file doesn't exist
    """
    # Implementation...
```

### Error Handling

- Use specific exception types, not bare `except:`
- Provide meaningful error messages with context
- Log errors appropriately using the standard library `logging`

### Configuration

- Use `tomllib` for reading TOML files (Python 3.11+) with `tomli` fallback
- Validate configuration with clear error messages
- Support both pyproject.toml and dedicated config files

## Architecture Patterns

### Core Modules

- `core.py`: Main recipe generation logic
- `cli.py`: Command-line interface using Click/Typer
- `_version.py`: Version management (auto-generated)

### Data Flow

1. **Input**: Python project metadata (pyproject.toml, setup.py, etc.)
2. **Processing**: Parse dependencies, detect build system, analyze project structure
3. **Output**: Generate conda-forge recipe YAML with proper formatting

## Review Checklist

### Code Changes

- [ ] Type hints are present and accurate
- [ ] Functions have descriptive docstrings
- [ ] Error handling is appropriate and specific
- [ ] No hardcoded paths or platform assumptions
- [ ] Logging is used instead of print statements

### Testing

- [ ] New functionality has corresponding tests
- [ ] Tests cover both success and failure scenarios
- [ ] Mock external dependencies (file system, network)
- [ ] Test data is realistic and representative

### Documentation

- [ ] README.md is updated for new features
- [ ] CHANGELOG.md entries follow conventional commits
- [ ] Code comments explain "why" not "what"
- [ ] Complex algorithms have clear explanations

### Dependencies

- [ ] New dependencies are justified and well-maintained
- [ ] Version constraints are appropriate (not overly restrictive)
- [ ] Dependencies are added to correct pixi feature groups
- [ ] Security implications are considered

## Common Issues to Flag

### Anti-Patterns

- Using `subprocess` without proper error handling
- Hardcoding file paths instead of using `pathlib.Path`
- Missing input validation on user-provided data
- Not handling optional dependencies gracefully

### Security Concerns

- Arbitrary code execution risks
- Unsafe file operations (path traversal)
- Unvalidated user input in shell commands
- Missing input sanitization

### Performance Issues

- Reading large files into memory unnecessarily
- Inefficient string concatenation in loops
- Not using appropriate data structures (sets vs lists)
- Blocking I/O operations without async handling

## Special Considerations

### Conda-forge Ecosystem

- Recipe format must comply with conda-forge standards
- Build numbers and version strings must be valid
- Dependencies should use conda-forge package names when available
- Platform selectors must be accurate

### Cross-Platform Compatibility

- File path handling must work on Windows, macOS, and Linux
- Use `pathlib.Path` instead of string manipulation
- Be aware of case sensitivity differences
- Handle line endings appropriately

### Integration Points

- pixi task definitions in pyproject.toml
- GitHub Actions workflows
- Pre-commit hook configuration
- VS Code settings and extensions

## Review Tone

- **Be constructive**: Suggest improvements with explanations
- **Be specific**: Reference exact lines and provide examples
- **Be educational**: Explain why changes improve the code
- **Be pragmatic**: Balance perfection with practical delivery
- **Be encouraging**: Acknowledge good patterns and improvements

## Questions to Ask

1. Does this change improve the user experience?
2. Is the code maintainable and readable?
3. Are there potential edge cases not covered?
4. Does this follow the project's architectural patterns?
5. Is the change backward compatible where needed?

Remember: The goal is to help maintain high code quality while supporting the developer's learning and the project's success.
