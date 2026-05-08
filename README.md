# CodeReview-Agent: Multi-Agent LLM Code Review System

An intelligent, automated code review system powered by LangGraph multi-agent architecture for bug detection, security analysis, and intelligent refactoring.

## 🚀 Features

- **Multi-Agent Architecture**: Specialized agents for different code review aspects using LangGraph
- **Comprehensive Analysis**:
  - Security vulnerability detection
  - Logic error identification
  - Anti-pattern recognition
  - Code quality assessment
- **Static Analysis Integration**: Pylint, Bandit, Flake8, and custom rule validators
- **Evaluation Framework**: Precision, Recall, F1-Score, Confusion Matrix metrics
- **Intelligent Refactoring**: AI-powered code optimization suggestions
- **RESTful API**: Scalable backend service for integration
- **Structured Reports**: Detailed review reports with quality scoring

## 📋 Architecture

```
┌─────────────────────────────────────────────┐
│          Code Review Orchestrator           │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼───────┐   ┌──────▼──────┐
│  Static       │   │  LLM Agent  │
│  Analysis     │   │  Graph      │
└───────┬───────┘   └──────┬──────┘
        │                   │
        │         ┌─────────┴──────────┐
        │         │                    │
        │  ┌──────▼──────┐  ┌─────────▼─────────┐
        │  │   Security  │  │   Refactoring     │
        │  │   Agent     │  │   Agent           │
        │  └─────────────┘  └───────────────────┘
        │         │                    │
        │  ┌──────▼──────┐  ┌─────────▼─────────┐
        │  │  Bug        │  │   Quality         │
        │  │  Detection  │  │   Scoring         │
        │  │  Agent      │  │   Agent           │
        │  └─────────────┘  └───────────────────┘
        │                                │
        └────────────────┬───────────────┘
                         │
                ┌────────▼─────────┐
                │   Evaluation     │
                │   Framework      │
                └──────────────────┘
```

## 🛠️ Installation

### Prerequisites

- Python 3.9+
- OpenAI API key or compatible LLM provider

### Setup

```bash
# Clone the repository
cd CodeReview-Agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

## 📖 Usage

### Command Line Interface

```bash
# Analyze a single file
python -m src.cli analyze --file path/to/code.py

# Analyze a directory
python -m src.cli analyze --dir path/to/project

# Generate report
python -m src.cli analyze --file code.py --report json
```

### API Service

```bash
# Start the backend service
python -m src.api.server

# Service runs on http://localhost:8000
```

### API Endpoints

```bash
# Submit code for review
POST /api/v1/review
{
  "code": "def example():\n    pass",
  "language": "python",
  "options": {
    "check_security": true,
    "check_bugs": true,
    "suggest_refactoring": true
  }
}

# Get review status
GET /api/v1/review/{review_id}

# Get evaluation metrics
GET /api/v1/metrics
```

### Python SDK

```python
from src.agents.orchestrator import CodeReviewOrchestrator
from src.core.config import Config

# Initialize
config = Config.from_env()
orchestrator = CodeReviewOrchestrator(config)

# Review code
result = orchestrator.review_code(
    code="""
    def calculate_total(items):
        total = 0
        for item in items:
            total = total + item
        return total
    """,
    language="python"
)

# Access results
print(f"Quality Score: {result.quality_score}/100")
print(f"Issues Found: {len(result.issues)}")
print(f"Refactoring Suggestions: {len(result.refactorings)}")
```

## 📊 Evaluation Metrics

The system tracks:

- **Precision**: Accuracy of detected issues
- **Recall**: Coverage of actual issues
- **F1-Score**: Harmonic mean of precision and recall
- **Confusion Matrix**: True/False Positives/Negatives
- **Hallucination Rate**: False positive detection rate

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run evaluation benchmarks
python -m src.evaluation.benchmark
```

## 📁 Project Structure

```
CodeReview-Agent/
├── src/
│   ├── agents/              # LangGraph multi-agent system
│   │   ├── security_agent.py
│   │   ├── bug_detector.py
│   │   ├── refactoring_agent.py
│   │   ├── quality_agent.py
│   │   └── orchestrator.py
│   ├── analysis/            # Static analysis tools
│   │   ├── static_analyzer.py
│   │   ├── rule_validator.py
│   │   └── patterns.py
│   ├── evaluation/          # Metrics and evaluation
│   │   ├── metrics.py
│   │   ├── confusion_matrix.py
│   │   └── benchmark.py
│   ├── api/                 # Backend service
│   │   ├── server.py
│   │   ├── routes.py
│   │   └── models.py
│   ├── core/                # Core utilities
│   │   ├── config.py
│   │   └── utils.py
│   └── cli.py               # Command-line interface
├── tests/
├── examples/
├── docs/
├── requirements.txt
├── .env.example
└── README.md
```

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- LangGraph for multi-agent orchestration
- Static analysis tools: Pylint, Bandit, Flake8
- OpenAI for LLM capabilities
