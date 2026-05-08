# API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication required for local development. For production deployment, implement API key authentication.

## Endpoints

### 1. Health Check

Check if the service is running.

**Endpoint**: `GET /health`

**Response**:

```json
{
  "status": "healthy",
  "orchestrator": "initialized"
}
```

---

### 2. Submit Code Review (Synchronous)

Submit code for review and wait for results.

**Endpoint**: `POST /api/v1/review/sync`

**Request Body**:

```json
{
  "code": "def example():\n    pass",
  "language": "python",
  "file_path": "example.py",
  "options": {
    "check_security": true,
    "check_bugs": true,
    "suggest_refactoring": true,
    "calculate_metrics": true
  }
}
```

**Parameters**:

- `code` (string, required): Source code to review
- `language` (string, required): Programming language (python, javascript, typescript, java, go)
- `file_path` (string, optional): File path for context
- `options` (object, optional): Review options
  - `check_security` (boolean): Enable security analysis
  - `check_bugs` (boolean): Enable bug detection
  - `suggest_refactoring` (boolean): Enable refactoring suggestions
  - `calculate_metrics` (boolean): Calculate quality metrics

**Response**: `200 OK`

```json
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "review_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-05-09T10:30:00.000Z",
    "language": "python",
    "code_hash": "abc123...",
    "issues": [
      {
        "id": "issue-1",
        "category": "security",
        "severity": "high",
        "title": "SQL Injection Risk",
        "description": "SQL query constructed using string concatenation",
        "line_start": 10,
        "line_end": 10,
        "code_snippet": "query = f\"SELECT * FROM users WHERE id = {user_id}\"",
        "recommendation": "Use parameterized queries",
        "confidence": 0.95,
        "source": "security_agent",
        "metadata": {}
      }
    ],
    "refactorings": [
      {
        "id": "refactor-1",
        "title": "Extract method",
        "description": "Function is too long, extract into smaller functions",
        "original_code": "def long_function():...",
        "refactored_code": "def smaller_function():...",
        "benefits": ["Improved readability", "Easier testing"],
        "line_start": 15,
        "line_end": 45,
        "priority": "medium",
        "confidence": 0.85
      }
    ],
    "quality_metrics": {
      "overall_score": 75,
      "maintainability": 70,
      "reliability": 80,
      "security": 65,
      "performance": 85,
      "complexity": 75,
      "test_coverage": null,
      "code_smells": 5,
      "technical_debt_minutes": 45
    },
    "total_lines": 100,
    "execution_time_seconds": 3.5,
    "status": "completed",
    "errors": []
  },
  "message": "Review completed successfully"
}
```

**Error Response**: `500 Internal Server Error`

```json
{
  "detail": "Review failed: <error message>"
}
```

---

### 3. Submit Code Review (Asynchronous)

Submit code for review, returns immediately with review ID.

**Endpoint**: `POST /api/v1/review`

**Request Body**: Same as synchronous endpoint

**Response**: `200 OK`

```json
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "result": null,
  "message": "Review submitted successfully. Use /review/{review_id} to check status."
}
```

---

### 4. Get Review Result

Retrieve review results by ID.

**Endpoint**: `GET /api/v1/review/{review_id}`

**Path Parameters**:

- `review_id` (string): Review identifier

**Response**: `200 OK`

```json
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    /* ReviewResult object */
  },
  "message": "Review status: completed"
}
```

**Status Values**:

- `processing`: Review in progress
- `completed`: Review finished successfully
- `failed`: Review encountered an error

**Error Response**: `404 Not Found`

```json
{
  "detail": "Review not found"
}
```

---

### 5. Get Review Status

Get only the status without full result.

**Endpoint**: `GET /api/v1/review/{review_id}/status`

**Path Parameters**:

- `review_id` (string): Review identifier

**Response**: `200 OK`

```json
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "Current status: completed"
}
```

---

### 6. List Reviews

List recent reviews with pagination.

**Endpoint**: `GET /api/v1/reviews`

**Query Parameters**:

- `limit` (integer, optional): Number of results (default: 10)
- `offset` (integer, optional): Offset for pagination (default: 0)

**Response**: `200 OK`

```json
{
  "total": 50,
  "limit": 10,
  "offset": 0,
  "reviews": [
    {
      "review_id": "550e8400-e29b-41d4-a716-446655440000",
      "language": "python",
      "timestamp": "2024-05-09T10:30:00",
      "status": "completed",
      "issues_count": 5,
      "quality_score": 75
    }
  ]
}
```

---

### 7. Get Metrics

Get aggregate metrics across all reviews.

**Endpoint**: `GET /api/v1/metrics`

**Response**: `200 OK`

```json
{
  "total_reviews": 150,
  "total_issues": 450,
  "average_quality_score": 72.5,
  "issues_by_severity": {
    "critical": 10,
    "high": 50,
    "medium": 150,
    "low": 200,
    "info": 40
  },
  "issues_by_category": {
    "security": 75,
    "bug": 120,
    "performance": 30,
    "maintainability": 180,
    "style": 45,
    "complexity": 0,
    "anti_pattern": 0,
    "logic_error": 0
  }
}
```

---

### 8. Delete Review

Delete a review by ID.

**Endpoint**: `DELETE /api/v1/review/{review_id}`

**Path Parameters**:

- `review_id` (string): Review identifier

**Response**: `200 OK`

```json
{
  "message": "Review 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

---

## Data Models

### ReviewRequest

```typescript
{
  code: string;           // Source code (required)
  language: string;       // Programming language (required)
  file_path?: string;     // Optional file path
  options?: {             // Optional review options
    check_security?: boolean;
    check_bugs?: boolean;
    suggest_refactoring?: boolean;
    calculate_metrics?: boolean;
  }
}
```

### CodeIssue

```typescript
{
  id: string;
  category: "security" | "bug" | "performance" | "maintainability" | "style" | "complexity" | "anti_pattern" | "logic_error";
  severity: "critical" | "high" | "medium" | "low" | "info";
  title: string;
  description: string;
  line_start?: number;
  line_end?: number;
  code_snippet?: string;
  recommendation?: string;
  confidence: number;     // 0.0 to 1.0
  source: string;
  metadata: object;
}
```

### RefactoringTask

```typescript
{
  id: string;
  title: string;
  description: string;
  original_code: string;
  refactored_code: string;
  benefits: string[];
  line_start?: number;
  line_end?: number;
  priority: "high" | "medium" | "low";
  confidence: number;     // 0.0 to 1.0
}
```

### QualityMetrics

```typescript
{
  overall_score: number;          // 0-100
  maintainability: number;        // 0-100
  reliability: number;            // 0-100
  security: number;               // 0-100
  performance: number;            // 0-100
  complexity: number;             // 0-100 (higher = simpler)
  test_coverage?: number;         // 0-100
  code_smells: number;
  technical_debt_minutes: number;
}
```

## Examples

### Python Client Example

```python
import requests

# Submit review
response = requests.post(
    "http://localhost:8000/api/v1/review/sync",
    json={
        "code": "def divide(a, b):\n    return a / b",
        "language": "python"
    }
)

result = response.json()
print(f"Quality Score: {result['result']['quality_metrics']['overall_score']}/100")
print(f"Issues: {len(result['result']['issues'])}")
```

### JavaScript/Node.js Example

```javascript
const axios = require("axios");

async function reviewCode() {
  const response = await axios.post(
    "http://localhost:8000/api/v1/review/sync",
    {
      code: "function divide(a, b) { return a / b; }",
      language: "javascript",
    },
  );

  console.log(
    `Quality Score: ${response.data.result.quality_metrics.overall_score}/100`,
  );
  console.log(`Issues: ${response.data.result.issues.length}`);
}

reviewCode();
```

### cURL Example

```bash
curl -X POST http://localhost:8000/api/v1/review/sync \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def example():\n    pass",
    "language": "python"
  }'
```

## Rate Limiting

- Default: 100 requests per minute per IP
- Configurable via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS`

## Error Handling

All errors return appropriate HTTP status codes:

- `400 Bad Request`: Invalid input
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

Error response format:

```json
{
  "detail": "Error message"
}
```

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
