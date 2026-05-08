"""Data models for code review system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(str, Enum):
    """Categories of code issues."""
    SECURITY = "security"
    BUG = "bug"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"
    COMPLEXITY = "complexity"
    ANTI_PATTERN = "anti_pattern"
    LOGIC_ERROR = "logic_error"


class CodeIssue(BaseModel):
    """Represents a single code issue found during review."""
    
    id: str = Field(..., description="Unique issue identifier")
    category: IssueCategory = Field(..., description="Issue category")
    severity: Severity = Field(..., description="Issue severity")
    title: str = Field(..., description="Short issue title")
    description: str = Field(..., description="Detailed description")
    line_start: Optional[int] = Field(None, description="Starting line number")
    line_end: Optional[int] = Field(None, description="Ending line number")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    recommendation: Optional[str] = Field(None, description="How to fix")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    source: str = Field(..., description="Detection source (agent/tool name)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RefactoringTask(BaseModel):
    """Represents a refactoring suggestion."""
    
    id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Refactoring title")
    description: str = Field(..., description="What to refactor and why")
    original_code: str = Field(..., description="Original code")
    refactored_code: str = Field(..., description="Suggested refactored code")
    benefits: List[str] = Field(default_factory=list, description="Benefits of refactoring")
    line_start: Optional[int] = Field(None, description="Starting line number")
    line_end: Optional[int] = Field(None, description="Ending line number")
    priority: Severity = Field(..., description="Refactoring priority")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Suggestion confidence")


class QualityMetrics(BaseModel):
    """Code quality metrics."""
    
    overall_score: int = Field(..., ge=0, le=100, description="Overall quality score")
    maintainability: int = Field(..., ge=0, le=100, description="Maintainability score")
    reliability: int = Field(..., ge=0, le=100, description="Reliability score")
    security: int = Field(..., ge=0, le=100, description="Security score")
    performance: int = Field(..., ge=0, le=100, description="Performance score")
    complexity: int = Field(..., ge=0, le=100, description="Complexity score (higher is simpler)")
    test_coverage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Test coverage %")
    code_smells: int = Field(0, ge=0, description="Number of code smells")
    technical_debt_minutes: int = Field(0, ge=0, description="Technical debt in minutes")


class ReviewResult(BaseModel):
    """Complete code review result."""
    
    review_id: str = Field(..., description="Unique review identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Review timestamp")
    language: str = Field(..., description="Programming language")
    code_hash: str = Field(..., description="Hash of reviewed code")
    
    # Results
    issues: List[CodeIssue] = Field(default_factory=list, description="Detected issues")
    refactorings: List[RefactoringTask] = Field(default_factory=list, description="Refactoring suggestions")
    quality_metrics: QualityMetrics = Field(..., description="Quality metrics")
    
    # Statistics
    total_lines: int = Field(0, ge=0, description="Total lines of code")
    execution_time_seconds: float = Field(0.0, ge=0.0, description="Review execution time")
    
    # Status
    status: str = Field("completed", description="Review status")
    errors: List[str] = Field(default_factory=list, description="Errors during review")
    
    def get_critical_issues(self) -> List[CodeIssue]:
        """Get critical severity issues."""
        return [issue for issue in self.issues if issue.severity == Severity.CRITICAL]
    
    def get_high_issues(self) -> List[CodeIssue]:
        """Get high severity issues."""
        return [issue for issue in self.issues if issue.severity == Severity.HIGH]
    
    def get_issues_by_category(self, category: IssueCategory) -> List[CodeIssue]:
        """Get issues by category."""
        return [issue for issue in self.issues if issue.category == category]
    
    def get_security_issues(self) -> List[CodeIssue]:
        """Get security-related issues."""
        return self.get_issues_by_category(IssueCategory.SECURITY)
    
    def get_bug_issues(self) -> List[CodeIssue]:
        """Get bug-related issues."""
        return [
            issue for issue in self.issues
            if issue.category in (IssueCategory.BUG, IssueCategory.LOGIC_ERROR)
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(indent=2)


class AgentState(BaseModel):
    """State passed between agents in LangGraph."""
    
    # Input
    code: str = Field(..., description="Code to review")
    language: str = Field(..., description="Programming language")
    file_path: Optional[str] = Field(None, description="Optional file path")
    options: Dict[str, Any] = Field(default_factory=dict, description="Review options")
    
    # Agent outputs
    security_issues: List[CodeIssue] = Field(default_factory=list)
    bug_issues: List[CodeIssue] = Field(default_factory=list)
    refactorings: List[RefactoringTask] = Field(default_factory=list)
    quality_metrics: Optional[QualityMetrics] = None
    
    # Metadata
    review_id: str = Field(..., description="Review session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


class ReviewRequest(BaseModel):
    """API request for code review."""
    
    code: str = Field(..., description="Code to review", min_length=1)
    language: str = Field(..., description="Programming language")
    file_path: Optional[str] = Field(None, description="Optional file path")
    options: Dict[str, bool] = Field(
        default_factory=lambda: {
            "check_security": True,
            "check_bugs": True,
            "suggest_refactoring": True,
            "calculate_metrics": True,
        },
        description="Review options"
    )


class ReviewResponse(BaseModel):
    """API response for code review."""
    
    review_id: str = Field(..., description="Review identifier")
    status: str = Field(..., description="Review status")
    result: Optional[ReviewResult] = Field(None, description="Review result if completed")
    message: Optional[str] = Field(None, description="Status message")
