# Security Policy

Security is very important for pyrattler-recipe-autogen and its community. 🔒

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

We encourage you to:

- [Write tests](https://github.com/millsks/pyrattler-recipe-autogen#testing) for your usage of pyrattler-recipe-autogen
- Update to the latest version frequently after ensuring your tests pass
- Review the [CHANGELOG](CHANGELOG.md) for security-related updates

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you believe you have found a security vulnerability in pyrattler-recipe-autogen, please report it privately using one of the following methods:

### Preferred: GitHub Security Advisories

Use [GitHub Security Advisories](https://github.com/millsks/pyrattler-recipe-autogen/security/advisories/new) to report vulnerabilities privately. This allows us to:

- Discuss the vulnerability privately
- Work on a fix before public disclosure
- Coordinate disclosure timing
- Issue security advisories when appropriate

### Alternative: Email

Send an email to: **<millsks@gmail.com>**

- Use "SECURITY: pyrattler-recipe-autogen vulnerability" in the subject line
- Include as much detail as possible (see details below)

### What to Include

Please try to be as explicit as possible, describing:

1. **Vulnerability Type**: What kind of security issue is this?
2. **Impact**: What could an attacker potentially do?
3. **Attack Vector**: How would someone exploit this?
4. **Affected Components**: Which parts of pyrattler-recipe-autogen are affected?
5. **Reproduction Steps**: Step-by-step instructions to reproduce the issue
6. **Environment**: OS, Python version, pyrattler-recipe-autogen version
7. **Proof of Concept**: Sample code or commands (without working exploits)
8. **Suggested Fix**: If you have ideas for how to address the issue

## Security Considerations

### Input Validation

pyrattler-recipe-autogen processes `pyproject.toml` files and generates recipe.yaml files. Key security considerations:

- **TOML Parsing**: We use Python's built-in `tomllib` for parsing TOML files
- **File System Access**: The tool reads from and writes to the file system based on user input
- **Subprocess Execution**: Limited subprocess usage for version detection (git, poetry, etc.)
- **Path Handling**: User-provided file paths are processed

### Potential Risk Areas

Areas where security vulnerabilities might occur:

1. **Path Traversal**: File path handling and validation
2. **Code Injection**: TOML content processing and YAML generation
3. **Command Injection**: Subprocess execution for tool detection
4. **Denial of Service**: Resource consumption during file processing
5. **Information Disclosure**: Error messages and debug output

## Security Response Process

When a security vulnerability is reported:

1. **Acknowledgment**: We'll acknowledge receipt within 48 hours
2. **Assessment**: We'll assess the vulnerability and determine severity
3. **Fix Development**: We'll work on a fix while maintaining confidentiality
4. **Testing**: We'll test the fix thoroughly
5. **Disclosure**: We'll coordinate disclosure timing with the reporter
6. **Release**: We'll release a security update and publish an advisory

### Timeline Expectations

- **Initial Response**: Within 48 hours
- **Assessment Complete**: Within 1 week
- **Fix Available**: Depends on complexity, typically 1-4 weeks
- **Public Disclosure**: After fix is released and users have time to update

## Public Discussions

Please **do not publicly discuss potential security vulnerabilities** until:

- A fix has been developed and released
- Sufficient time has passed for users to update
- We've coordinated the disclosure timing

This helps limit the potential impact and protects users who haven't yet updated.

## Security Best Practices for Users

When using pyrattler-recipe-autogen:

1. **Keep Updated**: Use the latest version when possible
2. **Validate Inputs**: Be cautious with `pyproject.toml` files from untrusted sources
3. **Review Outputs**: Check generated recipe.yaml files before use
4. **Sandbox Usage**: Consider running in isolated environments for untrusted inputs
5. **Report Issues**: Report any suspicious behavior or potential security issues

## Recognition

We appreciate security researchers and users who responsibly disclose vulnerabilities. Contributors who report valid security issues will be:

- Credited in the security advisory (unless they prefer to remain anonymous)
- Mentioned in release notes
- Added to our security acknowledgments

## Questions?

If you have questions about this security policy or need clarification on reporting procedures, please open a [GitHub Discussion](https://github.com/millsks/pyrattler-recipe-autogen/discussions) or email <millsks@gmail.com>.

---

Thank you for helping keep pyrattler-recipe-autogen and our community safe! 🙏
