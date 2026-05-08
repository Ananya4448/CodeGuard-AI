# Architecture Guide

## Overview

CodeReview-Agent is a multi-agent LLM system designed to automate code review processes using LangGraph for orchestration and specialized AI agents for different review aspects.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   User Interface Layer                   │
│  (CLI, REST API, Python SDK)                            │
└────────────────────┬───────────────────────────────────┘
                     │
┌────────────────────▼───────────────────────────────────┐
│              Code Review Orchestrator                   │
│              (LangGraph Workflow)                       │
└────────────────────┬───────────────────────────────────┘
                     │
        ┌────────────┴──────────────┐
        │                           │
┌───────▼───────┐          ┌───────▼────────┐
│  Static       │          │  LLM Agent     │
│  Analysis     │          │  Layer         │
│  Layer        │          │                │
└───────┬───────┘          └───────┬────────┘
        │                           │
        │         ┌─────────────────┴──────────────┐
        │         │                                 │
        │  ┌──────▼──────┐                  ┌──────▼──────┐
        │  │  Security   │                  │ Refactoring │
        │  │  Agent      │                  │ Agent       │
        │  └─────────────┘                  └─────────────┘
        │         │                                 │
        │  ┌──────▼──────┐                  ┌──────▼──────┐
        │  │  Bug        │                  │  Quality    │
        │  │  Detection  │                  │  Scoring    │
        │  │  Agent      │                  │  Agent      │
        │  └─────────────┘                  └─────────────┘
        │                                           │
        └───────────────────┬───────────────────────┘
                            │
                   ┌────────▼─────────┐
                   │   Evaluation     │
                   │   Framework      │
                   └──────────────────┘
```

## Core Components

### 1. Code Review Orchestrator

**Location**: `src/agents/orchestrator.py`

**Responsibilities**:

- Coordinates the multi-agent workflow using LangGraph
- Manages agent execution order and dependencies
- Aggregates results from all agents
- Handles error recovery and fallback mechanisms

**LangGraph Workflow**:

```python
workflow = StateGraph(AgentState)

# Define agent nodes
workflow.add_node("security", security_analysis)
workflow.add_node("bug_detection", bug_detection)
workflow.add_node("refactoring", refactoring_analysis)
workflow.add_node("quality", quality_scoring)

# Define execution flow
workflow.set_entry_point("security")
workflow.add_edge("security", "bug_detection")
workflow.add_conditional_edges("bug_detection", should_refactor)
workflow.add_edge("refactoring", "quality")
workflow.add_edge("quality", END)
```

### 2. Specialized Agents

#### Security Agent

**Location**: `src/agents/security_agent.py`

**Purpose**: Detect security vulnerabilities and unsafe patterns

**Capabilities**:

- SQL injection detection
- Cross-Site Scripting (XSS) vulnerabilities
- Hardcoded credentials
- Unsafe deserialization
- Command injection
- Cryptographic weaknesses

**Implementation**:

- Uses LLM for context-aware analysis
- Pattern matching for known vulnerabilities
- Integration with Bandit for Python security analysis

#### Bug Detection Agent

**Location**: `src/agents/bug_detector.py`

**Purpose**: Identify logic errors and potential runtime bugs

**Capabilities**:

- Null pointer/None reference errors
- Array index out of bounds
- Off-by-one errors
- Resource leaks
- Race conditions
- Incorrect exception handling

**Implementation**:

- LLM-powered semantic analysis
- AST (Abstract Syntax Tree) analysis
- Pattern-based detection

#### Refactoring Agent

**Location**: `src/agents/refactoring_agent.py`

**Purpose**: Suggest code improvements and refactorings

**Capabilities**:

- Code smell detection
- Design pattern recommendations
- Complexity reduction suggestions
- Code duplication identification
- SOLID principle violations

**Implementation**:

- LLM-generated refactoring suggestions
- Provides before/after code examples
- Prioritizes suggestions by impact

#### Quality Scoring Agent

**Location**: `src/agents/quality_agent.py`

**Purpose**: Calculate comprehensive quality metrics

**Capabilities**:

- Overall quality score (0-100)
- Maintainability index
- Reliability score
- Security score
- Performance score
- Complexity metrics

**Implementation**:

- Aggregates findings from all agents
- Uses LLM for holistic quality assessment
- Calculates technical debt estimates

### 3. Static Analysis Layer

**Location**: `src/analysis/`

**Components**:

- **StaticAnalyzer**: Integrates Pylint, Flake8, Bandit, MyPy
- **RuleValidator**: Pattern-based rule engine
- **AntiPatternDetector**: AST-based anti-pattern detection
- **ComplexityAnalyzer**: Cyclomatic complexity, Halstead metrics

**Integration**:

```python
static_analyzer = StaticAnalyzer(config)
issues = static_analyzer.analyze(code, language)

rule_validator = RuleValidator()
rule_issues = rule_validator.validate(code, language)
```

### 4. Evaluation Framework

**Location**: `src/evaluation/`

**Components**:

- **MetricsCalculator**: Calculates precision, recall, F1-score
- **ConfusionMatrix**: Tracks TP, FP, TN, FN
- **Benchmark**: Evaluation against ground truth datasets

**Metrics**:

```python
class ConfusionMatrix:
    - Precision = TP / (TP + FP)
    - Recall = TP / (TP + FN)
    - F1-Score = 2 * (Precision * Recall) / (Precision + Recall)
    - Hallucination Rate = FP / (FP + TN)
```

### 5. Backend API Service

**Location**: `src/api/`

**Technology**: FastAPI + Uvicorn

**Endpoints**:

- `POST /api/v1/review/sync`: Synchronous review
- `POST /api/v1/review`: Asynchronous review
- `GET /api/v1/review/{id}`: Get review results
- `GET /api/v1/metrics`: Aggregate metrics

**Features**:

- RESTful API design
- Background task processing
- CORS support
- Rate limiting
- API documentation (Swagger/OpenAPI)

## Data Flow

### Review Request Flow

1. **Input**: Code + Language + Options
2. **Orchestrator**: Initialize AgentState
3. **Security Agent**: Analyze for vulnerabilities → Update state
4. **Bug Detection Agent**: Identify bugs → Update state
5. **Refactoring Agent**: Generate suggestions → Update state
6. **Quality Agent**: Calculate metrics → Update state
7. **Output**: ReviewResult with all findings

### State Management

```python
@dataclass
class AgentState:
    code: str
    language: str
    security_issues: List[CodeIssue]
    bug_issues: List[CodeIssue]
    refactorings: List[RefactoringTask]
    quality_metrics: QualityMetrics
    errors: List[str]
```

## Design Patterns

### 1. Chain of Responsibility

Agents process code sequentially, each adding their findings to shared state.

### 2. Strategy Pattern

Different analysis strategies (LLM, static analysis, pattern matching) can be swapped.

### 3. Observer Pattern

Evaluation framework observes agent outputs to calculate metrics.

### 4. Factory Pattern

Configuration factory creates appropriate LLM instances based on provider.

## Scalability Considerations

### Horizontal Scaling

- Stateless API design
- Background task queue (Celery/RQ for production)
- Result caching (Redis)
- Database for persistent storage

### Performance Optimization

- Parallel agent execution (future enhancement)
- LLM response caching
- Incremental analysis for large codebases
- Timeout management

### Resource Management

- Configurable concurrent review limits
- Agent timeout settings
- Memory-efficient code parsing
- Streaming results for large outputs

## Security

### Input Validation

- Code size limits
- Language validation
- Sanitization of file paths

### API Security

- API key authentication (production)
- Rate limiting
- CORS configuration
- Input sanitization

### LLM Security

- API key management via environment variables
- Request/response validation
- Timeout protection
- Error handling to prevent data leaks

## Extensibility

### Adding New Agents

1. Create agent class inheriting base pattern
2. Implement `analyze(state: AgentState) -> AgentState`
3. Register in orchestrator workflow
4. Update graph edges

### Adding New Languages

1. Update `supported_languages` in config
2. Add language-specific rules in RuleValidator
3. Add static analysis tool integration
4. Update detection patterns

### Custom Rules

```python
validator.add_custom_rule(
    language="python",
    name="custom_rule",
    pattern=r"pattern",
    category=IssueCategory.SECURITY,
    severity=Severity.HIGH,
    title="Title",
    description="Description",
    recommendation="Fix suggestion"
)
```

## Deployment

### Development

```bash
python -m src.api.server
```

### Production

```bash
# Using Gunicorn
gunicorn src.api.server:app -w 4 -k uvicorn.workers.UvicornWorker

# Using Docker
docker build -t codereview-agent .
docker run -p 8000:8000 codereview-agent
```

### Environment Variables

See `.env.example` for all configuration options.

## Monitoring & Observability

### Logging

- Structured logging with Loguru
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log rotation and compression

### Metrics

- Review count and success rate
- Average execution time
- Issue detection rates
- Quality score distribution

### Tracing

- LangSmith integration for LLM call tracing
- Request/response logging
- Performance profiling

## Future Enhancements

1. **Multi-language Support**: Expand beyond Python
2. **Incremental Analysis**: Analyze only changed code
3. **CI/CD Integration**: GitHub Actions, GitLab CI plugins
4. **Machine Learning**: Train custom models for issue detection
5. **Interactive Mode**: Chat-based code review
6. **Team Features**: Collaborative review, shared configurations
7. **IDE Plugins**: VSCode, IntelliJ extensions
