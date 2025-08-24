# Release Process

This document describes how to create and publish releases for pyrattler-recipe-autogen.

## 🚀 **Quick Release**

1. **Go to GitHub Actions** → `Release and Publish` workflow
2. **Click "Run workflow"**
3. **Fill in the form**:

   - **Version**: e.g., `1.0.0` (semantic versioning)
   - **Pre-release**: ✅ for alpha/beta/rc versions
   - **Publish to PyPI**: ✅ (recommended for production releases)
   - **Publish to Test PyPI**: ✅ (optional, for testing)

4. **Click "Run workflow"** and wait for completion

## ✨ **What happens automatically:**

### 🔍 **Quality Assurance**

- ✅ Runs linting (ruff)
- ✅ Type checking (mypy)
- ✅ Security scanning (bandit)
- ✅ Full test suite with coverage
- ✅ Builds package and verifies artifacts

### 🏗️ **Release Creation**

- ✅ Updates `CHANGELOG.md` with new version
- ✅ Creates git tag and commit
- ✅ Pushes changes to main branch

### 📦 **Publishing** (if enabled)

- ✅ Publishes to Test PyPI (if requested)
- ✅ Tests installation from Test PyPI
- ✅ Publishes to PyPI (production)
- ✅ Creates GitHub release with assets

### 📋 **Release Notes**

- ✅ Auto-generated with version info
- ✅ Quality metrics summary
- ✅ Installation instructions
- ✅ Includes all build artifacts

## 🔧 **Manual Steps (if needed)**

### Test PyPI Verification

```bash
# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ \
           --extra-index-url https://pypi.org/simple/ \
           pyrattler-recipe-autogen==1.0.0

# Verify installation
python -c "import pyrattler_recipe_autogen; print(pyrattler_recipe_autogen.__version__)"
```

### Production Installation

```bash
# Install from PyPI
pip install pyrattler-recipe-autogen==1.0.0

# Verify installation
python -c "import pyrattler_recipe_autogen; print(pyrattler_recipe_autogen.__version__)"
```

## 📋 **Version Guidelines**

### Semantic Versioning

- **Major** (`1.0.0`): Breaking changes
- **Minor** (`0.1.0`): New features, backward compatible
- **Patch** (`0.0.1`): Bug fixes, backward compatible

### Pre-release Tags

- **Alpha** (`1.0.0-alpha.1`): Early development
- **Beta** (`1.0.0-beta.1`): Feature complete, testing phase
- **RC** (`1.0.0-rc.1`): Release candidate

## 🚨 **Troubleshooting**

### Failed Quality Checks

- Check the workflow logs for specific failures
- Fix issues and re-run the workflow
- Common issues: linting errors, test failures, type errors

### PyPI Publishing Issues

- Verify API tokens are configured in repository secrets:
  - `PYPI_API_TOKEN`: Production PyPI
  - `TEST_PYPI_API_TOKEN`: Test PyPI
- Ensure version doesn't already exist on PyPI

### Git Push Issues

- Workflow runs with elevated permissions
- Should not have conflicts if main branch is up to date
- Check repository protection rules

## 🔐 **Security**

- All publishing uses **trusted publishing** (OIDC)
- No API tokens stored in workflow files
- Secrets are configured at repository level
- Environment protection rules apply for PyPI

## 🎯 **Best Practices**

1. **Always test first**: Use Test PyPI for verification
2. **Follow semantic versioning**: Clear version increments
3. **Review changes**: Check what's included in the release
4. **Monitor workflow**: Watch for any failures or issues
5. **Verify installation**: Test the published package

---

**Need help?** Check the workflow logs or open an issue for assistance.
