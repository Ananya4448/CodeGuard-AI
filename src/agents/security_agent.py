"""Security analysis agent for detecting vulnerabilities."""

import uuid
from typing import List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from loguru import logger

from src.agents.models import AgentState, CodeIssue, IssueCategory, Severity
from src.core.config import Config


class SecurityAgent:
    """Agent specialized in security vulnerability detection."""
    
    def __init__(self, config: Config):
        """Initialize security agent."""
        self.config = config
        llm_config = config.get_llm_config()
        
        self.llm = ChatOpenAI(
            model=llm_config["model"],
            api_key=llm_config["api_key"],
            temperature=0.1,
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert security analyst specialized in finding security vulnerabilities in code.

Analyze the provided code for security issues including but not limited to:
- SQL injection vulnerabilities
- Cross-Site Scripting (XSS) vulnerabilities
- Cross-Site Request Forgery (CSRF) issues
- Insecure deserialization
- Authentication and authorization flaws
- Cryptographic weaknesses
- Hardcoded credentials or secrets
- Path traversal vulnerabilities
- Command injection
- Insecure random number generation
- Unvalidated redirects
- Information disclosure
- Race conditions
- Denial of Service vulnerabilities

For each security issue found, provide:
1. Severity (critical/high/medium/low)
2. Title (brief description)
3. Detailed description
4. Line numbers (if applicable)
5. Code snippet showing the vulnerability
6. Recommendation for fixing
7. Confidence level (0.0 to 1.0)

Return your analysis as a JSON array of issues. Be thorough but avoid false positives.
Focus on real security risks, not style issues."""),
            ("user", """Language: {language}

Code to analyze:
```{language}
{code}
```

Provide security analysis in JSON format:
[
  {{
    "severity": "critical|high|medium|low",
    "title": "Brief title",
    "description": "Detailed description",
    "line_start": 10,
    "line_end": 15,
    "code_snippet": "vulnerable code",
    "recommendation": "How to fix",
    "confidence": 0.95
  }}
]""")
        ])
    
    def analyze(self, state: AgentState) -> AgentState:
        """Analyze code for security vulnerabilities."""
        logger.info(f"Security agent analyzing code (review_id: {state.review_id})")
        
        try:
            # Use LLM to detect security issues
            chain = self.prompt | self.llm
            response = chain.invoke({
                "code": state.code,
                "language": state.language
            })
            
            # Parse LLM response
            issues = self._parse_llm_response(response.content)
            
            # Add to state
            state.security_issues.extend(issues)
            
            logger.info(f"Security agent found {len(issues)} security issues")
            
        except Exception as e:
            logger.error(f"Security agent error: {e}")
            state.errors.append(f"Security analysis error: {str(e)}")
        
        return state
    
    def _parse_llm_response(self, response_text: str) -> List[CodeIssue]:
        """Parse LLM response into CodeIssue objects."""
        import json
        import re
        
        issues = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                logger.warning("No JSON array found in security agent response")
                return issues
            
            data = json.loads(json_match.group())
            
            for item in data:
                issue = CodeIssue(
                    id=str(uuid.uuid4()),
                    category=IssueCategory.SECURITY,
                    severity=Severity(item.get("severity", "medium")),
                    title=item.get("title", "Security Issue"),
                    description=item.get("description", ""),
                    line_start=item.get("line_start"),
                    line_end=item.get("line_end"),
                    code_snippet=item.get("code_snippet"),
                    recommendation=item.get("recommendation"),
                    confidence=float(item.get("confidence", 0.8)),
                    source="security_agent",
                )
                issues.append(issue)
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse security agent JSON response: {e}")
        except Exception as e:
            logger.error(f"Error parsing security agent response: {e}")
        
        return issues


# Fallback function for basic security checks (when LLM is not available)
def basic_security_check(code: str, language: str) -> List[CodeIssue]:
    """Basic pattern-based security checks."""
    issues = []
    
    # Python-specific checks
    if language == "python":
        patterns = {
            r"eval\(": ("Use of eval()", "Avoid using eval() as it can execute arbitrary code", Severity.HIGH),
            r"exec\(": ("Use of exec()", "Avoid using exec() as it can execute arbitrary code", Severity.HIGH),
            r"pickle\.loads": ("Unsafe deserialization", "pickle.loads can execute arbitrary code", Severity.CRITICAL),
            r"os\.system\(": ("Command injection risk", "os.system() is vulnerable to command injection", Severity.HIGH),
            r"subprocess\.call\(.+shell=True": ("Shell injection risk", "Using shell=True is dangerous", Severity.HIGH),
            r"password\s*=\s*['\"][^'\"]+['\"]": ("Hardcoded password", "Passwords should not be hardcoded", Severity.CRITICAL),
            r"api_key\s*=\s*['\"][^'\"]+['\"]": ("Hardcoded API key", "API keys should not be hardcoded", Severity.CRITICAL),
        }
        
        for pattern, (title, desc, severity) in patterns.items():
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    id=str(uuid.uuid4()),
                    category=IssueCategory.SECURITY,
                    severity=severity,
                    title=title,
                    description=desc,
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=match.group(),
                    recommendation=f"Replace with secure alternative",
                    confidence=0.7,
                    source="pattern_matcher",
                ))
    
    return issues
