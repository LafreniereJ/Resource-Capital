# Contributing to Mining Intelligence System

Thank you for your interest in contributing to the Mining Intelligence System! This document provides guidelines and information for contributors.

## 🎯 Code of Conduct

By participating in this project, you agree to abide by our code of conduct:
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow ethical data collection practices

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Git installed and configured
- Virtual environment knowledge
- Basic understanding of web scraping ethics

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/mining-intelligence-system.git
   cd mining-intelligence-system
   ```

2. **Set up Development Environment**
   ```bash
   python -m venv mining_env
   source mining_env/bin/activate  # On Windows: mining_env\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your development configuration
   ```

4. **Run Tests**
   ```bash
   python -m pytest tests/ -v
   ```

## 🌿 Branching Strategy

We follow a Git Flow branching model:

### Main Branches
- **`main`**: Production-ready code
- **`develop`**: Integration branch for features

### Feature Branches
- **`feature/core-system`**: Core system modifications
- **`feature/web-scrapers`**: New scrapers or scraper improvements
- **`feature/data-processors`**: Data processing enhancements
- **`feature/intelligence-modules`**: Business intelligence features
- **`feature/reporting`**: Report generation improvements

### Branch Naming Convention
```
feature/short-description
bugfix/issue-description
hotfix/critical-fix-description
docs/documentation-update
```

### Workflow
1. Create feature branch from `develop`
2. Make changes and commit
3. Submit pull request to `develop`
4. After review and approval, merge to `develop`
5. Periodic releases merge `develop` to `main`

## 📝 Coding Standards

### Python Style Guide
- Follow PEP 8 guidelines
- Use Black for code formatting: `black src/ tests/`
- Use isort for import sorting: `isort src/ tests/`
- Maximum line length: 88 characters

### Documentation Standards
- Include docstrings for all public functions and classes
- Use Google-style docstrings
- Add type hints for function parameters and return values
- Update README.md for significant changes

### Example Function Documentation
```python
def extract_company_data(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Extract comprehensive data from a company website.
    
    Args:
        url: The company website URL to scrape
        timeout: Maximum time to wait for page load in seconds
        
    Returns:
        Dictionary containing extracted company data including:
        - basic_info: Company name, ticker, etc.
        - financial_data: Revenue, market cap, etc.
        - news: Recent news articles
        
    Raises:
        requests.RequestException: If URL cannot be accessed
        ValueError: If URL format is invalid
    """
```

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for module interactions
└── fixtures/       # Test data and mock responses
```

### Writing Tests
- Use pytest as the testing framework
- Aim for 80%+ code coverage
- Mock external API calls and web requests
- Include both positive and negative test cases

### Test Example
```python
import pytest
from unittest.mock import Mock, patch
from src.scrapers.enhanced_mining_scraper import EnhancedMiningScraper

class TestEnhancedMiningScraper:
    def test_extract_data_success(self):
        scraper = EnhancedMiningScraper()
        # Test implementation
        
    @patch('requests.get')
    def test_extract_data_network_error(self, mock_get):
        mock_get.side_effect = requests.RequestException()
        # Test implementation
```

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/unit/test_scrapers.py

# Run tests with verbose output
python -m pytest -v
```

## 📦 Module Guidelines

### Adding New Scrapers (`src/scrapers/`)
1. Inherit from a base scraper class
2. Implement required methods: `extract_data()`, `validate_data()`
3. Include proper error handling and rate limiting
4. Add comprehensive tests
5. Update documentation

### Data Processors (`src/processors/`)
1. Follow single responsibility principle
2. Include data validation and cleaning
3. Handle missing or malformed data gracefully
4. Add progress logging for long operations

### Intelligence Modules (`src/intelligence/`)
1. Focus on specific analysis areas
2. Include confidence scores for insights
3. Document analysis methodology
4. Provide clear output formats

## 🔒 Security & Ethics

### Data Collection Ethics
- Respect robots.txt files
- Implement proper rate limiting
- Don't overload target servers
- Comply with website terms of service

### Security Practices
- Never commit API keys or credentials
- Use environment variables for sensitive data
- Validate and sanitize all inputs
- Follow OWASP security guidelines

### Privacy Considerations
- Only collect publicly available data
- Implement data retention policies
- Respect user privacy rights
- Document data usage clearly

## 🐛 Issue Reporting

### Bug Reports
Include the following information:
- Python version and operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Relevant log files or error messages
- Minimal code example if applicable

### Feature Requests
- Describe the problem you're trying to solve
- Explain why this feature would be valuable
- Provide examples of how it would be used
- Consider implementation complexity

## 📋 Pull Request Process

### Before Submitting
1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new functionality
4. Run code formatting tools
5. Check for security issues

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No sensitive data included
```

### Review Process
1. Automated tests must pass
2. Code review by maintainers
3. Documentation review if applicable
4. Final approval and merge

## 🎖️ Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Annual contributor appreciation

## 📞 Getting Help

- **Questions**: Use GitHub Discussions
- **Issues**: Create GitHub Issues
- **Chat**: Join our development Discord (link in README)

## 📚 Resources

### Documentation
- [Python Official Documentation](https://docs.python.org/)
- [Playwright Documentation](https://playwright.dev/python/)
- [SQLite Documentation](https://sqlite.org/docs.html)

### Tools
- [Black Code Formatter](https://black.readthedocs.io/)
- [pytest Testing Framework](https://pytest.org/)
- [pre-commit Hooks](https://pre-commit.com/)

Thank you for contributing to making mining industry intelligence more accessible and comprehensive!