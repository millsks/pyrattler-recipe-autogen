# GitHub Actions Local Testing with Act

This document explains how to use the `act` tasks for local GitHub Actions testing.

## Available Act Tasks

### Setup

- `pixi run act-setup` - Initialize act configuration files

### Basic Usage

- `pixi run act` - Run act with default settings (pass additional args)
- `pixi run act-list` - List all available workflows and jobs
- `pixi run act-dryrun` - Show what would run without executing

### Workflow-Specific Tasks

- `pixi run act-release` - Test the release workflow locally
- `pixi run act-publish` - Test the publish workflow locally
- `pixi run act-maintenance` - Test the maintenance workflow locally
- `pixi run act-release-test` - Test release workflow with sample inputs

## Getting Started

### 1. First-Time Setup

```bash
# Initialize act configuration
pixi run act-setup

# This creates:
# - .actrc (act configuration)
# - .secrets (dummy secrets for testing)
```

### 2. Basic Testing

```bash
# List available workflows
pixi run act-list

# Dry run to see what would execute
pixi run act-dryrun

# Test a specific workflow
pixi run act-release
```

### 3. Passing Custom Arguments

Since pixi tasks can accept additional arguments, you can customize act execution:

```bash
# Run with specific inputs
pixi run act workflow_dispatch -W .github/workflows/release.yml \
  --input version=1.0.0 \
  --input prerelease=false

# Run with different platform
pixi run act --platform ubuntu-latest=ubuntu:20.04

# Run specific job only
pixi run act -j build

# Run with verbose output
pixi run act -v

# Run without pulling Docker images
pixi run act --pull=false
```

### 4. Environment Variables and Secrets

Edit `.secrets` file to add real tokens if needed:

```bash
GITHUB_TOKEN=ghp_your_real_token
RELEASE_PAT=ghp_your_pat_token
TEST_PYPI_API_TOKEN=your_test_pypi_token
PYPI_API_TOKEN=your_pypi_token
```

## Common Use Cases

### Test Release Workflow

```bash
# Quick syntax check
pixi run act-dryrun

# Test with sample version
pixi run act-release-test

# Test with custom version
pixi run act workflow_dispatch -W .github/workflows/release.yml \
  --input version=0.11.0 \
  --input force_recreate=true
```

### Test Publish Workflow

```bash
# Simulate release published event
pixi run act-publish

# Test with specific release data
pixi run act release -W .github/workflows/publish.yml \
  --eventpath .github/event-payloads/release.json
```

### Debug Workflow Issues

```bash
# Run with maximum verbosity
pixi run act -v workflow_dispatch -W .github/workflows/release.yml

# Run specific step only
pixi run act --job release --step "Build package"

# Use different Docker image
pixi run act --platform ubuntu-latest=catthehacker/ubuntu:act-latest
```

## Configuration Files

### .actrc

```
# Use larger Docker image with more tools
-P ubuntu-latest=catthehacker/ubuntu:act-latest

# Use secrets file
--secret-file .secrets

# Default to verbose output
-v
```

### .secrets

```
GITHUB_TOKEN=dummy
RELEASE_PAT=dummy
TEST_PYPI_API_TOKEN=dummy
PYPI_API_TOKEN=dummy
```

## Limitations

- **Docker required**: Act runs workflows in Docker containers
- **Limited runners**: Not all GitHub-hosted runner features available
- **Secrets**: Use dummy values for testing, real secrets for full testing
- **Network**: Some network-dependent steps may behave differently

## Troubleshooting

### Common Issues

1. **Docker permission errors**: Ensure Docker is running and accessible
2. **Image pull failures**: Use `--pull=false` or specify different image
3. **Missing tools**: Use larger Docker image (`catthehacker/ubuntu:act-latest`)
4. **Secret errors**: Check `.secrets` file format and permissions

### Debug Commands

```bash
# Check act version
pixi run act --version

# List available Docker images
docker images | grep act

# Clean act cache
pixi run act --rm
```

## Integration with Development Workflow

### Before Pushing Changes

```bash
# Quick validation
pixi run actionlint

# Local testing
pixi run act-dryrun

# Full workflow test
pixi run act-release-test
```

### Testing Workflow Changes

```bash
# Test modified workflow
git add .github/workflows/release.yml
pixi run act workflow_dispatch -W .github/workflows/release.yml

# Compare with previous version
git stash
pixi run act-release  # test old version
git stash pop
pixi run act-release  # test new version
```

This setup allows you to iterate quickly on workflow changes without creating multiple commits or triggering actual releases!
