# Contributing to Digital Signal Intelligence

Thank you for your interest in contributing to the Digital Signal Intelligence (DSI) project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Getting Help](#getting-help)

## Code of Conduct

This project adheres to professional standards of conduct. All contributors are expected to:
- Be respectful and constructive in all interactions
- Focus on what is best for the project and community
- Show empathy towards other contributors
- Accept constructive criticism gracefully

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Docker (optional, for containerised development)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/digital-signal-intelligence.git
   cd digital-signal-intelligence
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/jwalker618/digital-signal-intelligence.git
   ```

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in editable mode
pip install -e .
```

### 3. Install Pre-commit Hooks

```bash
pre-commit install
```

This will automatically run code quality checks before each commit.

### 4. Verify Installation

```bash
# Run tests
pytest tests/ -v

# Start API server
uvicorn infrastructure.api.main:app --reload --port 8000
```

## Development Workflow

### 1. Create a Branch

Always create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications

### 2. Make Changes

- Write clear, concise commit messages
- Keep commits focused and atomic
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests

Before committing, ensure all tests pass:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=signal_architecture --cov=infrastructure --cov=layers --cov=coverages --cov-report=html

# Run specific test file
pytest tests/unit/test_workflow.py -v

# Run linting
flake8 signal_architecture/ infrastructure/ layers/ coverages/
black --check signal_architecture/ infrastructure/ layers/ coverages/
isort --check-only signal_architecture/ infrastructure/ layers/ coverages/
mypy signal_architecture/ infrastructure/ layers/
```

### 4. Commit Changes

```bash
git add .
git commit -m "Clear description of changes"
```

Pre-commit hooks will automatically run. Fix any issues they identify.

## Coding Standards

### Python Style

We follow PEP 8 with some modifications:
- Line length: 100 characters (not 79)
- Use Black for formatting
- Use isort for import sorting
- Type hints are encouraged but not required

### Code Quality Tools

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Bandit**: Security checks

### Documentation

- Use docstrings for all public classes and functions
- Follow Google-style docstring format
- Update README.md when adding new features
- Add examples for new functionality

Example docstring:
```python
def calculate_premium(self, profile: CompanyProfile) -> PricingResult:
    """
    Calculate insurance premium based on company profile.

    Args:
        profile: Company profile containing signals and attributes

    Returns:
        PricingResult containing premium, tier, and recommendations

    Raises:
        ValueError: If profile contains invalid data
    """
```

## Testing Guidelines

### Test Structure

- Place tests in `tests/` directories within each model
- Name test files `test_*.py`
- Use pytest fixtures for reusable test data
- Aim for >80% code coverage

### Writing Tests

```python
def test_feature_description():
    """Test that feature works as expected"""
    # Arrange
    input_data = create_test_data()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result.expected_attribute == expected_value
```

### Test Categories

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test component interactions
3. **API Tests**: Test API endpoints
4. **Performance Tests**: Ensure acceptable performance

### Running Specific Tests

```bash
# Run tests for specific area
pytest tests/unit/ -v

# Run tests matching pattern
pytest -k "test_pricing"

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=signal_architecture --cov=infrastructure --cov=layers --cov=coverages --cov-report=term-missing
```

## Submitting Changes

### 1. Update Your Branch

```bash
git fetch upstream
git rebase upstream/main
```

### 2. Push Changes

```bash
git push origin your-branch-name
```

### 3. Create Pull Request

1. Go to GitHub and create a Pull Request
2. Fill in the PR template with:
   - Description of changes
   - Related issues
   - Testing performed
   - Screenshots (if applicable)

### 4. Code Review

- Address reviewer feedback promptly
- Make requested changes in new commits
- Once approved, squash commits if requested

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] PR description is complete
- [ ] No merge conflicts

## Project Structure

```
digital-signal-intelligence/
├── signal_architecture/    # Signal processing (signals, discovery, orchestration, graph, multiplexer)
├── infrastructure/         # Support systems (api, db, analytics, builder, integrations)
├── layers/                 # Assessment layers (risk, exposure, loss)
├── coverages/              # YAML coverage configurations (10 coverages)
├── tests/                  # Test suite (unit, integration, api, performance)
├── deploy/                 # Deployment configs (Docker, Kubernetes, monitoring)
├── demo/                   # Interactive demos and examples
├── rust/                   # Rust performance modules (dsi-core, dsi-sim)
├── docs/                   # Documentation and case studies
├── development/            # Phase development plans and assessments
└── .github/                # CI/CD workflows
```

## Adding New Features

### New Coverage Configuration

1. Create new directory under `coverages/` (e.g. `coverages/new_coverage/`)
2. Add `config.yaml` following `coverages/master_config_layout.yaml` schema
3. Add inference functions in `signal_architecture/signals/inference/functions/`
4. Add stub extractors in `signal_architecture/signals/extractors/stubs/`
5. Run `python coverages/doc_generator.py` to generate `logic.md`
6. Add comprehensive tests
7. Update documentation

### New API Endpoint

1. Add route in `infrastructure/api/routes/`
2. Define request/response models in `infrastructure/api/types.py`
3. Add API tests in `tests/api/`
4. Update OpenAPI documentation
5. Add usage example

## Performance Guidelines

- Optimize for readability first, performance second
- Profile before optimizing
- Document performance-critical sections
- Add performance tests for critical paths

## Security Guidelines

- Never commit secrets or API keys
- Use environment variables for configuration
- Run security checks with Bandit
- Follow OWASP guidelines for web security

## Getting Help

- **Questions**: Open an issue with the `question` label
- **Bugs**: Open an issue with detailed reproduction steps
- **Features**: Open an issue to discuss before implementing
- **Contact**: john.walker@example.com

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (Proprietary License).

## Recognition

Contributors will be recognized in the project README and release notes.

---

Thank you for contributing to Digital Signal Intelligence!
