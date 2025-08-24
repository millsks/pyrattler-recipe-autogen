# Contributing to pyrattler-recipe-autogen

Thank you for your interest in contributing to pyrattler-recipe-autogen! This document provides guidelines and information for contributors.

## 🚀 Quick Start

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

3. **Run Tests**:

   ```bash
   pixi run test-cov
   ```

4. **Make Changes** and test thoroughly

5. **Submit Pull Request**

## 📋 Development Requirements

### Prerequisites

- [Pixi](https://pixi.sh) - Modern package management
- Git for version control
- Python 3.9+ (managed by pixi)

### Required Tools (Installed by pixi)

- **pytest**: Testing framework
- **mypy**: Static type checking
- **ruff**: Code formatting and linting
- **bandit**: Security analysis
- **pre-commit**: Git hooks for quality assurance
- **coverage**: Test coverage analysis

## 🏗️ Development Setup

### Initial Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/pyrattler-recipe-autogen.git
cd pyrattler-recipe-autogen

# Add upstream remote
git remote add upstream https://github.com/millsks/pyrattler-recipe-autogen.git

# Install dependencies (includes editable install)
pixi install

# Setup development environment
pixi run dev-setup
```

### Development Environment

The project uses pixi for all development tasks:

```bash
# Format code
pixi run format

# Run linting
pixi run lint

# Run type checking
pixi run type-check

# Run security checks
pixi run security-check

# Run all quality checks (lint + type-check)
pixi run check

# Run all quality checks including security (lint + type-check + security-check)
pixi run check-all

# Run tests
pixi run test

# Run tests with coverage
pixi run test-cov

# Run full CI pipeline
pixi run ci
```

## 🧪 Testing Guidelines

### Writing Tests

- **Location**: Place tests in `tests/` directory
- **Naming**: Test files should start with `test_`
- **Coverage**: Aim for >95% test coverage
- **Types**: Include unit tests, integration tests, and edge cases

### Test Structure

```python
def test_function_name():
    """Test description explaining what is being tested."""
    # Arrange - Set up test data
    input_data = {...}
    expected_result = {...}

    # Act - Call the function being tested
    result = function_under_test(input_data)

    # Assert - Verify the result
    assert result == expected_result
```

### Running Tests

```bash
# Run all tests
pixi run test

# Run specific test file
pixi run python -m pytest tests/test_core.py

# Run specific test function
pixi run python -m pytest tests/test_core.py::test_function_name

# Run with coverage
pixi run test-cov

# Run with verbose output
pixi run python -m pytest -xvs
```

## 🎨 Code Style Guidelines

### Code Formatting

We use **ruff** for code formatting and linting:

```bash
# Format code automatically
pixi run format

# Check for linting issues
pixi run lint
```

### Type Annotations

- **Required**: All functions must have type annotations
- **Imports**: Use `from __future__ import annotations` for modern syntax
- **Complex Types**: Use `typing` module for complex types
- **Return Types**: Always specify return types, use `None` for procedures

Example:

```python
from __future__ import annotations

def process_data(data: dict[str, Any], options: list[str]) -> tuple[bool, str]:
    """Process data with given options."""
    # Implementation
    return success, message
```

### Docstring Standards

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of the function.

    Longer description if needed, explaining the function's purpose,
    behavior, and any important details.

    Args:
        param1: Description of the first parameter.
        param2: Description of the second parameter.

    Returns:
        Description of what the function returns.

    Raises:
        ValueError: Description of when this exception is raised.
        TypeError: Description of when this exception is raised.

    Example:
        >>> result = function_name("hello", 42)
        >>> print(result)
        True
    """
    # Implementation
```

## 🔄 Git Workflow

### Branch Naming

Use descriptive branch names with prefixes:

- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test improvements

Examples:

- `feat/integration-enhancements`
- `fix/dependency-mapping-bug`
- `docs/readme-improvements`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to build process or auxiliary tools

Examples:

```bash
git commit -m "feat: add pixi integration detection"
git commit -m "fix: resolve dependency mapping for numpy"
git commit -m "docs: update README with new examples"
git commit -m "test: add integration tests for CI/CD detection"
```

### Pull Request Process

1. **Update Your Fork**:

   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create Feature Branch**:

   ```bash
   git checkout -b feat/your-feature-name
   ```

3. **Make Changes**:

   - Write code
   - Add tests
   - Update documentation
   - Ensure all quality checks pass

4. **Quality Checks**:

   ```bash
   pixi run ci  # Runs format + check + test-cov
   ```

5. **Commit Changes**:

   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push Branch**:

   ```bash
   git push origin feat/your-feature-name
   ```

7. **Create Pull Request**:
   - Use descriptive title
   - Explain changes in description
   - Reference related issues
   - Include testing information

## 📝 Pull Request Guidelines

### PR Title

Use conventional commit format:

```
feat: add integration enhancements functionality
fix: resolve issue with dynamic version detection
docs: improve README examples and configuration
```

### PR Description Template

```markdown
## Description

Brief description of the changes made.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing

- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have tested the changes manually

## Checklist

- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] Any dependent changes have been merged and published

## Related Issues

Fixes #(issue number)
Related to #(issue number)
```

## 🐛 Reporting Issues

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:

1. Run command '...'
2. With input file '...'
3. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Environment:**

- OS: [e.g. macOS, Linux, Windows]
- Python version: [e.g. 3.9]
- pyrattler-recipe-autogen version: [e.g. 0.1.0]

**Additional context**
Add any other context about the problem here.
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.
```

## 🔍 Code Review Process

### Review Criteria

Reviewers will check:

1. **Functionality**: Does the code work as intended?
2. **Tests**: Are there adequate tests with good coverage?
3. **Documentation**: Are docstrings and comments clear?
4. **Style**: Does the code follow project conventions?
5. **Performance**: Are there any performance concerns?
6. **Breaking Changes**: Will this break existing functionality?

### Addressing Review Comments

1. Make requested changes
2. Push new commits to the same branch
3. Respond to comments explaining changes
4. Request re-review when ready

## 🏆 Recognition

Contributors will be:

- Listed in the README acknowledgments
- Credited in release notes for significant contributions
- Considered for maintainer status for sustained contributions

## 📚 Resources

### Documentation

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

### Tools

- [Pixi Documentation](https://pixi.sh/latest/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)

## ❓ Getting Help

- **Questions**: Use [GitHub Discussions](https://github.com/millsks/pyrattler-recipe-autogen/discussions)
- **Issues**: Report bugs via [GitHub Issues](https://github.com/millsks/pyrattler-recipe-autogen/issues)
- **Chat**: Join our development discussions

## 📜 Code of Conduct

This project follows a Code of Conduct based on the [Contributor Covenant](https://www.contributor-covenant.org/). By participating, you are expected to uphold this code.

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone,
regardless of age, body size, disability, ethnicity, gender identity and expression,
level of experience, nationality, personal appearance, race, religion, or sexual
identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

---

Thank you for contributing to pyrattler-recipe-autogen! 🚀
