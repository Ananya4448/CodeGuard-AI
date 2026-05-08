# Contributing to CodeReview-Agent

Thank you for your interest in contributing to CodeReview-Agent! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect differing opinions and experiences

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- OpenAI API key or compatible LLM provider

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/CodeReview-Agent.git
   cd CodeReview-Agent
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run Tests**
   ```bash
   pytest
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes

### 2. Make Changes

- Write clean, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific tests
pytest tests/test_agents.py::test_security_agent
```

### 4. Commit Changes

Write clear, descriptive commit messages:

```bash
git commit -m "feat: add support for TypeScript analysis"
git commit -m "fix: resolve issue with async review processing"
git commit -m "docs: update API documentation"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Build/tooling changes

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Link to related issues
- Screenshots (if UI changes)
- Test results

## Code Style Guidelines

### Python Style

Follow PEP 8 and use these tools:

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Check style
flake8 src/ tests/

# Type checking
mypy src/
```

### Code Standards

- **Maximum line length**: 100 characters
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Imports**: Group by standard library, third-party, local
- **Type hints**: Use type hints for function parameters and return values

Example:
```python
from typing import List, Optional

def analyze_code(
    code: str,
    language: str,
    options: Optional[Dict[str, bool]] = None
) -> ReviewResult:
    """
    Analyze code for issues.
    
    Args:
        code: Source code to analyze
        language: Programming language
        options: Optional analysis options
    
    Returns:
        ReviewResult with findings
    """
    # Implementation
    pass
```

### Documentation

- **Docstrings**: Use Google-style docstrings
- **Comments**: Explain why, not what
- **README**: Update if adding features
- **API docs**: Update for API changes

## Testing Guidelines

### Writing Tests

```python
import pytest
from src.agents.security_agent import SecurityAgent

def test_security_agent_detects_sql_injection():
    """Test that security agent detects SQL injection."""
    config = Config.from_env()
    agent = SecurityAgent(config)
    
    code = """
    def get_user(user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        return execute(query)
    """
    
    state = AgentState(code=code, language="python", review_id="test")
    result = agent.analyze(state)
    
    assert len(result.security_issues) > 0
    assert any("injection" in issue.title.lower() for issue in result.security_issues)
```

### Test Coverage

- Aim for >80% code coverage
- Test edge cases and error conditions
- Test both success and failure paths
- Mock external dependencies (LLM calls)

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_agents.py

# With coverage
pytest --cov=src --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Adding New Features

### Adding a New Agent

1. Create agent file in `src/agents/`
2. Inherit from base pattern or create new pattern
3. Implement `analyze(state: AgentState) -> AgentState`
4. Update orchestrator to include new agent
5. Add tests in `tests/test_agents.py`
6. Update documentation

Example:
```python
# src/agents/performance_agent.py
class PerformanceAgent:
    def __init__(self, config: Config):
        self.config = config
        self.llm = create_llm(config)
    
    def analyze(self, state: AgentState) -> AgentState:
        # Analyze code for performance issues
        issues = self._detect_performance_issues(state.code)
        state.performance_issues.extend(issues)
        return state
```

### Adding Language Support

1. Add language to `supported_languages` in config
2. Add rules in `src/analysis/rule_validator.py`
3. Update static analysis integration
4. Add language-specific patterns
5. Update documentation

### Adding Custom Rules

See `examples/custom_rules.py` for example.

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Added tests for new features
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- Change 1
- Change 2

## Testing
- Test scenario 1
- Test scenario 2

## Related Issues
Closes #123

## Screenshots (if applicable)
```

### Review Process

1. Automated checks run (tests, linting)
2. Code review by maintainers
3. Address feedback
4. Approval and merge

## Reporting Issues

### Bug Reports

Include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)
- Error messages and stack traces
- Minimal code example

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Potential impact

## Project Structure

```
CodeReview-Agent/
├── src/
│   ├── agents/         # Multi-agent system
│   ├── analysis/       # Static analysis
│   ├── evaluation/     # Metrics and evaluation
│   ├── api/           # Backend service
│   ├── core/          # Core utilities
│   └── cli.py         # CLI interface
├── tests/             # Test suite
├── examples/          # Usage examples
├── docs/              # Documentation
└── requirements.txt   # Dependencies
```

## Development Tools

### Recommended VS Code Extensions

- Python
- Pylance
- Python Test Explorer
- GitLens
- Better Comments

### Useful Commands

```bash
# Format code
make format  # if Makefile exists
black src/ tests/
isort src/ tests/

# Run linters
flake8 src/
pylint src/

# Type checking
mypy src/

# Build distribution
python -m build

# Install in development mode
pip install -e .
```

## Questions?

- Open an issue for discussion
- Check existing issues and PRs
- Read documentation in `docs/`

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

Thank you for contributing! 🎉
