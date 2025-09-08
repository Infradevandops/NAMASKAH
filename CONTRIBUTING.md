# Contributing to CumApp

Thank you for your interest in contributing to CumApp! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Git
- API keys for Twilio, TextVerified, and Groq

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/Infradevandops/CumApp.git
   cd CumApp
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Docker Development**
   ```bash
   ./docker-dev.sh dev
   ```

4. **Local Development** (Alternative)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

## 📋 Development Guidelines

### Code Style
- Follow PEP 8 Python style guide
- Use type hints for function parameters and return values
- Write docstrings for all functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

### Code Formatting
```bash
# Install development tools
pip install black isort flake8 mypy

# Format code
black .
isort .

# Check style
flake8 .
mypy .
```

### Testing
- Write tests for all new features
- Maintain test coverage above 80%
- Use pytest for testing
- Mock external API calls in tests

```bash
# Run tests
pytest tests/ -v --cov=app

# Run specific test
pytest tests/test_textverified.py -v
```

## 🔄 Contribution Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Write code following the guidelines above
- Add tests for new functionality
- Update documentation if needed

### 3. Test Your Changes
```bash
# Run all tests
pytest

# Test with Docker
./docker-dev.sh build
./docker-dev.sh health
```

### 4. Commit Changes
```bash
git add .
git commit -m "feat: add new feature description"
```

### Commit Message Format
Use conventional commits format:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 🏗 Project Structure

```
CumApp/
├── main.py                 # FastAPI application
├── textverified_client.py  # TextVerified API client
├── groq_client.py         # Groq AI client
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Multi-service setup
├── tests/               # Test files
├── static/              # Static assets
├── templates/           # HTML templates
├── .kiro/              # Kiro IDE specifications
└── docs/               # Documentation
```

## 🧪 Testing Guidelines

### Test Categories
1. **Unit Tests** - Test individual functions/classes
2. **Integration Tests** - Test API endpoints
3. **E2E Tests** - Test complete workflows

### Writing Tests
```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_textverified_client():
    # Mock external API calls
    pass
```

### Test Data
- Use fixtures for test data
- Mock external API responses
- Don't use real API keys in tests

## 📚 Documentation

### Code Documentation
- Write clear docstrings
- Include parameter types and descriptions
- Provide usage examples

```python
async def create_verification(service_name: str, capability: str = "sms") -> str:
    """
    Create a verification using TextVerified API.
    
    Args:
        service_name: Name of the service (e.g., 'whatsapp')
        capability: Type of verification ('sms', 'voice')
    
    Returns:
        Verification ID string
        
    Raises:
        HTTPException: If verification creation fails
        
    Example:
        >>> verification_id = await create_verification("whatsapp")
        >>> print(verification_id)
        "abc123"
    """
```

### API Documentation
- FastAPI automatically generates OpenAPI docs
- Add descriptions to endpoints
- Include example requests/responses

## 🐛 Bug Reports

When reporting bugs, include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs
- API keys status (without revealing actual keys)

## 💡 Feature Requests

For new features:
- Describe the use case
- Explain the expected behavior
- Consider backward compatibility
- Discuss implementation approach

## 🔒 Security

### Reporting Security Issues
- **DO NOT** create public issues for security vulnerabilities
- Email security issues to: [security@yourcompany.com]
- Include detailed description and reproduction steps

### Security Guidelines
- Never commit API keys or secrets
- Use environment variables for configuration
- Validate all user inputs
- Follow OWASP security practices

## 📋 Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] Tests are written and passing
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] No sensitive data in commits
- [ ] Docker build succeeds
- [ ] Health checks pass

## 🏷 Release Process

### Version Numbering
We use Semantic Versioning (SemVer):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes

### Release Steps
1. Update version in relevant files
2. Update CHANGELOG.md
3. Create release branch
4. Test thoroughly
5. Create GitHub release
6. Deploy to production

## 🤝 Community

### Communication
- GitHub Issues for bugs and features
- GitHub Discussions for questions
- Discord/Slack for real-time chat (if available)

### Code of Conduct
- Be respectful and inclusive
- Help others learn and grow
- Focus on constructive feedback
- Follow GitHub's community guidelines

## 📞 Getting Help

If you need help:
1. Check existing documentation
2. Search GitHub issues
3. Ask in GitHub Discussions
4. Contact maintainers

## 🙏 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Invited to maintainer team (for significant contributions)

Thank you for contributing to CumApp! 🚀