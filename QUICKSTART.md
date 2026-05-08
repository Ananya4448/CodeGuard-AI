# Quick Start Guide

Get started with CodeReview-Agent in 5 minutes!

## Installation

### 1. Clone or Navigate to Project

```bash
cd CodeReview-Agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

**Required**: Set at minimum your `OPENAI_API_KEY` in the `.env` file.

## Usage

### Option 1: Python SDK (Simplest)

Create a file `my_review.py`:

```python
from src.agents.orchestrator import CodeReviewOrchestrator
from src.core.config import Config

# Initialize
config = Config.from_env()
orchestrator = CodeReviewOrchestrator(config)

# Your code to review
code = """
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item['price']
    return total
"""

# Review it
result = orchestrator.review_code(code, language="python")

# Check results
print(f"Quality Score: {result.quality_metrics.overall_score}/100")
print(f"Issues Found: {len(result.issues)}")

for issue in result.issues:
    print(f"- [{issue.severity.value}] {issue.title}")
```

Run it:

```bash
python my_review.py
```

### Option 2: Command Line

Review a single file:

```bash
python -m src.cli analyze --file example.py
```

Review a directory:

```bash
python -m src.cli analyze --dir src/
```

Generate JSON report:

```bash
python -m src.cli analyze --file app.py --report json --output report.json
```

### Option 3: REST API

Start the server:

```bash
python -m src.api.server
```

In another terminal, submit a review:

```bash
curl -X POST http://localhost:8000/api/v1/review/sync \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def example():\n    pass",
    "language": "python"
  }'
```

Or open http://localhost:8000/docs for interactive API documentation.

## Examples

### Basic Usage

```bash
python examples/basic_usage.py
```

### API Usage

```bash
# Start server first
python -m src.api.server

# In another terminal
python examples/api_usage.py
```

### Custom Rules

```bash
python examples/custom_rules.py
```

### Batch Processing

```bash
python examples/batch_processing.py src/
```

## Understanding the Output

### Quality Score (0-100)

- **90-100**: Excellent code quality
- **75-89**: Good quality
- **60-74**: Acceptable quality
- **Below 60**: Needs improvement

### Issue Severity Levels

- **Critical**: Must fix immediately (security vulnerabilities, critical bugs)
- **High**: Should fix soon (potential bugs, poor practices)
- **Medium**: Should address (code smells, maintainability issues)
- **Low**: Nice to fix (style issues, minor improvements)
- **Info**: Informational (suggestions, documentation)

### Example Output

```
==============================================================
CODE REVIEW REPORT
==============================================================

Quality Score: 65/100

--- ISSUES FOUND ---
Total Issues: 3

CRITICAL (1):
  [security] Hardcoded Password
    Line 12: Password should not be hardcoded in source code
    → Use environment variables or secure configuration

HIGH (1):
  [security] Unsafe eval() Usage
    Line 9: eval() can execute arbitrary code
    → Use ast.literal_eval() or refactor to avoid eval

MEDIUM (1):
  [bug] Bare Except Clause
    Line 20: Catching all exceptions can hide bugs
    → Catch specific exception types

--- REFACTORING SUGGESTIONS ---
1. Extract method from long function
   Lines 30-75: Function is 45 lines, consider breaking into smaller functions
   Benefits: Improved readability, Easier testing
```

## Common Use Cases

### 1. Pre-Commit Hook

Review code before committing:

```bash
python -m src.cli analyze --file changed_file.py
```

### 2. CI/CD Integration

Add to your GitHub Actions or GitLab CI:

```yaml
- name: Code Review
  run: |
    pip install -r requirements.txt
    python -m src.cli analyze --dir src/ --report json --output review.json
```

### 3. Code Quality Dashboard

Use the API to build a dashboard:

```python
import requests

response = requests.get("http://localhost:8000/api/v1/metrics")
metrics = response.json()

print(f"Average Quality: {metrics['average_quality_score']}")
print(f"Critical Issues: {metrics['issues_by_severity']['critical']}")
```

### 4. Refactoring Workflow

1. Review code before refactoring
2. Perform refactoring
3. Review again
4. Compare results

```bash
# Before refactoring
python examples/batch_processing.py src/ before.json

# After refactoring
python examples/batch_processing.py src/ after.json

# Compare
python examples/batch_processing.py compare before.json after.json
```

## Configuration

Edit `.env` to customize:

```bash
# LLM Provider
MODEL_PROVIDER=openai
MODEL_NAME=gpt-4-turbo-preview

# Enable/Disable Features
ENABLE_SECURITY_ANALYSIS=true
ENABLE_BUG_DETECTION=true
ENABLE_REFACTORING=true

# Static Analysis Tools
PYLINT_ENABLED=true
FLAKE8_ENABLED=true
BANDIT_ENABLED=true

# API Configuration
API_PORT=8000
```

## Troubleshooting

### "ModuleNotFoundError"

```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### "OpenAI API Key Error"

```bash
# Check .env file has your key
OPENAI_API_KEY=sk-your-actual-key-here

# Make sure .env is in the project root
ls -la .env  # Should exist
```

### "Rate Limit Error"

- You've hit OpenAI's rate limit
- Wait a moment and try again
- Or use a different API key

### Server Won't Start

```bash
# Check if port 8000 is in use
# Windows
netstat -ano | findstr :8000

# Mac/Linux
lsof -i :8000

# Use different port
API_PORT=8080 python -m src.api.server
```

## Next Steps

- Read [Architecture Guide](docs/ARCHITECTURE.md) to understand the system
- Check [API Documentation](docs/API.md) for API details
- See [Contributing Guide](CONTRIBUTING.md) to contribute
- Run benchmarks: `python -m src.cli benchmark`

## Need Help?

- Check the [README](README.md) for detailed documentation
- Look at [examples/](examples/) for more code samples
- Open an issue on GitHub for bugs or questions

---

**Happy Code Reviewing! 🚀**
