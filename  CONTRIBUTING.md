# Contributing to FastAPI Route

Thank you for your interest in contributing to FastAPI Route! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and constructive environment for everyone.

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:

- Check the issue tracker to see if the problem has already been reported
- Make sure you're using the latest version of FastAPI Route
- Try to reproduce the issue with a minimal example

When submitting a bug report, include:

- Your operating system and Python version
- FastAPI Route version
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Any relevant error messages or logs

### Suggesting Enhancements

When suggesting an enhancement:

- Clearly describe the feature and its use case
- Explain why this feature would be valuable to others
- If possible, provide examples of how the feature would work

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure everything passes
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git

### Setting Up Your Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/fastapi-route.git
cd fastapi-route

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
./scripts/test.sh

# Run tests without coverage
pytest tests/ -v

# Run a specific test file
pytest tests/test_core/test_scanner.py -v

# Run a specific test
pytest tests/test_core/test_scanner.py::TestRouteScanner::test_scan_valid_routes -v
```

### Code Style

This project follows PEP 8 with these additional guidelines:

- Use 4 spaces for indentation (no tabs)
- Maximum line length is 100 characters
- Use descriptive variable names
- Add docstrings for all public functions, classes, and modules
- Use type hints for function parameters and return values

### Running Linters

```bash
# Run black for code formatting
black fastapi_route/ tests/

# Run isort for import sorting
isort fastapi_route/ tests/

# Run ruff for linting
ruff check fastapi_route/ tests/
```

## Project Structure

```
fastapi-route/
├── fastapi_route/          # Main package source code
│   ├── __init__.py
│   ├── app.py               # Main application class
│   ├── core/                # Core routing logic
│   ├── routing/             # Route discovery and matching
│   ├── config/              # Configuration management
│   ├── build/               # Build and cache system
│   ├── dev/                 # Development server
│   ├── docs/                # Documentation generation
│   ├── middleware/          # Middleware management
│   ├── custom/              # Custom handlers
│   ├── static/              # Static file serving
│   ├── cli/                 # Command line interface
│   └── utils/               # Utility functions
├── tests/                   # Test suite
├── scripts/                 # Helper scripts
├── pyproject.toml           # Project configuration
└── README.md
```

## Adding New Features

### Adding a New Configuration Option

1. Add the option to the appropriate config class in `types.py`
2. Update `config/loader.py` to handle the new option
3. Update `config/validator.py` if validation is needed
4. Update the default config template in `config/loader.py`
5. Add documentation in the README

### Adding a New CLI Command

1. Add the command parser in `cli/commands.py`
2. Implement the command logic
3. Add the command to the `commands` dictionary in the default config
4. Update the README with the new command

### Adding a New Route Pattern Type

1. Update `constants.py` with any new pattern markers
2. Modify `core/scanner.py` to recognize the new pattern
3. Update `routing/matcher.py` to handle the new pattern if needed
4. Add tests for the new pattern

## Testing Guidelines

### Writing Tests

- Place tests in the `tests/` directory matching the source structure
- Use descriptive test names that explain what is being tested
- Each test should focus on a single behavior
- Use fixtures from `conftest.py` for common setup
- Mock external dependencies when appropriate

### Test Coverage

Aim to maintain or improve test coverage. Run coverage reports with:

```bash
pytest --cov=fastapi_route --cov-report=html tests/
open htmlcov/index.html
```

## Documentation

### Updating README

When adding features, update the README accordingly:

- Add new features to the Features section
- Update examples if needed
- Update CLI commands if applicable

### Code Documentation

- Use docstrings for all public functions and classes
- Follow Google-style docstring format
- Include type hints in docstrings
- Document exceptions that may be raised

Example docstring:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong
    """
```

## Release Process

1. Update version in `version.py`
2. Update CHANGELOG.md with new changes
3. Create a pull request for the release
4. After merge, tag the release
5. Build and publish to PyPI

## Getting Help

- Open an issue for bugs or feature requests
- Join discussions in existing issues
- Contact the maintainers directly

## Maintainers

- Abolfazl Hosseini - [@inject3r](https://github.com/inject3r)

## Recognition

Contributors will be acknowledged in the README and release notes.

Thank you for contributing!
