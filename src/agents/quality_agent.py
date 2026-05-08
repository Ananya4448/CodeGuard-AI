"""Quality scoring agent for code quality assessment."""

from typing import Optional

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from loguru import logger

from src.agents.models import AgentState, QualityMetrics
from src.core.config import Config
from src.core.utils import calculate_cyclomatic_complexity, count_lines


class QualityAgent:
    """Agent specialized in calculating code quality metrics."""
    
    def __init__(self, config: Config):
        """Initialize quality agent."""
        self.config = config
        llm_config = config.get_llm_config()
        
        self.llm = ChatOpenAI(
            model=llm_config["model"],
            api_key=llm_config["api_key"],
            temperature=0.0,  # Deterministic for metrics
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert code quality analyst.

Evaluate the provided code and assign scores (0-100) for:
1. **Maintainability**: How easy is the code to understand and modify?
2. **Reliability**: How robust and error-free is the code?
3. **Security**: How secure is the code from vulnerabilities?
4. **Performance**: How efficient is the code?
5. **Complexity**: How simple is the code? (100 = very simple, 0 = very complex)

Also estimate:
- **Code smells**: Number of code smells detected
- **Technical debt**: Estimated minutes to fix all issues

Provide scores based on:
- Code structure and organization
- Naming conventions
- Error handling
- Documentation
- Best practices adherence
- Design patterns usage
- Code duplication
- Function/method length
- Class cohesion

Return your assessment as JSON."""),
            ("user", """Language: {language}

Code to evaluate:
```{language}
{code}
```

Issues found: {issue_count}
Critical issues: {critical_count}
Security issues: {security_count}

Provide quality scores in JSON format:
{{
  "maintainability": 75,
  "reliability": 80,
  "security": 70,
  "performance": 85,
  "complexity": 65,
  "code_smells": 5,
  "technical_debt_minutes": 45
}}""")
        ])
    
    def analyze(self, state: AgentState) -> AgentState:
        """Calculate quality metrics."""
        logger.info(f"Quality agent calculating metrics (review_id: {state.review_id})")
        
        try:
            # Count existing issues
            all_issues = state.security_issues + state.bug_issues
            critical_count = sum(1 for issue in all_issues if issue.severity.value == "critical")
            security_count = len(state.security_issues)
            
            # Use LLM to calculate quality scores
            chain = self.prompt | self.llm
            response = chain.invoke({
                "code": state.code,
                "language": state.language,
                "issue_count": len(all_issues),
                "critical_count": critical_count,
                "security_count": security_count,
            })
            
            # Parse LLM response
            metrics = self._parse_llm_response(response.content, state)
            
            # Add to state
            state.quality_metrics = metrics
            
            logger.info(f"Quality agent calculated overall score: {metrics.overall_score}/100")
            
        except Exception as e:
            logger.error(f"Quality agent error: {e}")
            state.errors.append(f"Quality scoring error: {str(e)}")
            # Provide fallback metrics
            state.quality_metrics = self._calculate_fallback_metrics(state)
        
        return state
    
    def _parse_llm_response(self, response_text: str, state: AgentState) -> QualityMetrics:
        """Parse LLM response into QualityMetrics."""
        import json
        import re
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                logger.warning("No JSON found in quality agent response")
                return self._calculate_fallback_metrics(state)
            
            data = json.loads(json_match.group())
            
            # Calculate overall score as weighted average
            overall = int(
                data.get("maintainability", 70) * 0.25 +
                data.get("reliability", 70) * 0.25 +
                data.get("security", 70) * 0.25 +
                data.get("performance", 70) * 0.15 +
                data.get("complexity", 70) * 0.10
            )
            
            return QualityMetrics(
                overall_score=overall,
                maintainability=data.get("maintainability", 70),
                reliability=data.get("reliability", 70),
                security=data.get("security", 70),
                performance=data.get("performance", 70),
                complexity=data.get("complexity", 70),
                code_smells=data.get("code_smells", 0),
                technical_debt_minutes=data.get("technical_debt_minutes", 0),
            )
        
        except Exception as e:
            logger.error(f"Error parsing quality metrics: {e}")
            return self._calculate_fallback_metrics(state)
    
    def _calculate_fallback_metrics(self, state: AgentState) -> QualityMetrics:
        """Calculate fallback metrics when LLM is unavailable."""
        all_issues = state.security_issues + state.bug_issues
        
        # Simple heuristic: start at 100, deduct points for issues
        base_score = 100
        
        for issue in all_issues:
            if issue.severity.value == "critical":
                base_score -= 15
            elif issue.severity.value == "high":
                base_score -= 10
            elif issue.severity.value == "medium":
                base_score -= 5
            else:
                base_score -= 2
        
        # Ensure minimum score
        base_score = max(0, base_score)
        
        # Calculate technical debt (5 minutes per issue on average)
        technical_debt = len(all_issues) * 5
        
        return QualityMetrics(
            overall_score=base_score,
            maintainability=base_score,
            reliability=max(0, base_score - len([i for i in all_issues if i.category.value == "bug"]) * 5),
            security=max(0, base_score - len(state.security_issues) * 10),
            performance=base_score,
            complexity=max(50, min(100, 100 - calculate_cyclomatic_complexity(state.code, state.language))),
            code_smells=len(all_issues),
            technical_debt_minutes=technical_debt,
        )


def calculate_basic_metrics(code: str, language: str, issues_count: int = 0) -> QualityMetrics:
    """Calculate basic quality metrics without LLM."""
    lines = count_lines(code)
    complexity = calculate_cyclomatic_complexity(code, language)
    
    # Simple scoring based on code metrics
    base_score = 100 - (issues_count * 5)
    base_score = max(0, min(100, base_score))
    
    complexity_score = max(0, min(100, 100 - (complexity * 5)))
    
    return QualityMetrics(
        overall_score=base_score,
        maintainability=base_score,
        reliability=base_score,
        security=base_score,
        performance=80,  # Default
        complexity=complexity_score,
        code_smells=issues_count,
        technical_debt_minutes=issues_count * 5,
    )
