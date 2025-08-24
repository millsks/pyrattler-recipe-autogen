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

### Creating a Pull Request

When you create a pull request, GitHub will automatically load our pull request template with comprehensive checklists and sections to fill out.

**[🚀 Create Pull Request](https://github.com/millsks/pyrattler-recipe-autogen/compare)**

### PR Title

Use conventional commit format:

```
feat: add integration enhancements functionality
fix: resolve issue with dynamic version detection
docs: improve README examples and configuration
```

### PR Template Structure

Our pull request template includes the following sections:

- **Description**: Brief overview of your changes
- **Type of Change**: Bug fix, new feature, breaking change, or documentation
- **Testing**: Confirmation that tests have been added/updated and pass
- **Quality Checks**: Comprehensive checklist including:
  - Code formatting (`pixi run format`)
  - Linting (`pixi run lint`)
  - Type checking (`pixi run type-check`)
  - Security checks (`pixi run security-check`)
  - Test coverage (`pixi run test-cov`) - must maintain >95%
  - All checks (`pixi run check-all`)
- **Code Review Checklist**: Self-review items
- **Related Issues**: Link to relevant GitHub issues
- **Additional Context**: Extra information, screenshots, etc.

### Quality Requirements

Before submitting a PR, ensure:

1. **All tests pass**: `pixi run test`
2. **Code coverage maintained**: Must stay above 95%
3. **All quality checks pass**: `pixi run check-all`
4. **Pre-commit hooks pass**: Automatic on commit
5. **Self-review completed**: Review your own changes first

## 🐛 Reporting Issues

> **🔒 Security Issues**: Do **NOT** report security vulnerabilities as public issues.  
> Use [GitHub Security Advisories](https://github.com/millsks/pyrattler-recipe-autogen/security/advisories/new) or see our [Security Policy](SECURITY.md) for private reporting instructions.

### 🐛 Bug Reports

When you encounter a bug, please use our bug report template to provide detailed information:

**[📝 Create Bug Report](https://github.com/millsks/pyrattler-recipe-autogen/issues/new?assignees=&labels=bug%2Ctriage&projects=&template=bug_report.yml&title=%5BBug%5D%3A+)**

The bug report template will ask for:

- **Bug Description**: Clear description of what went wrong
- **Steps to Reproduce**: Exact steps to trigger the bug
- **Expected vs Actual Behavior**: What should have happened vs what actually happened
- **Environment Details**: OS, Python version, pyrattler-recipe-autogen version
- **Additional Context**: Logs, screenshots, or other helpful information

### ✨ Feature Requests

Have an idea for a new feature or enhancement? Use our feature request template:

**[💡 Create Feature Request](https://github.com/millsks/pyrattler-recipe-autogen/issues/new?assignees=&labels=enhancement%2Ctriage&projects=&template=feature_request.yml&title=%5BFeature%5D%3A+)**

The feature request template will guide you through:

- **Problem Statement**: What problem does this solve?
- **Proposed Solution**: Detailed description of your idea
- **Alternative Solutions**: Other approaches you've considered
- **Use Cases**: How would this feature be used?
- **Implementation Ideas**: Technical suggestions (if any)

### 💬 Questions and Discussions

For general questions, usage help, or community discussions:

- **[GitHub Discussions](https://github.com/millsks/pyrattler-recipe-autogen/discussions)**: Best for open-ended questions and community interaction
- **[Documentation](README.md)**: Check existing documentation first
- **[Examples](README.md#examples)**: Review usage examples

### 📋 Issue Guidelines

**Before Creating an Issue:**

1. **Search existing issues** to avoid duplicates
2. **Check the documentation** for existing solutions
3. **Use the appropriate template** (bug report vs feature request)
4. **Be specific and detailed** in your descriptions

**Writing Good Issues:**

- Use clear, descriptive titles
- Include all requested information from the template
- Add relevant labels if you have permission
- Reference related issues when applicable
- Update the issue if you find additional information

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
