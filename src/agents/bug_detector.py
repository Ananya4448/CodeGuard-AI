"""Bug detection agent for identifying logic errors and potential bugs."""

import uuid
from typing import List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from loguru import logger

from src.agents.models import AgentState, CodeIssue, IssueCategory, Severity
from src.core.config import Config


class BugDetectorAgent:
    """Agent specialized in detecting bugs and logic errors."""
    
    def __init__(self, config: Config):
        """Initialize bug detector agent."""
        self.config = config
        llm_config = config.get_llm_config()
        
        self.llm = ChatOpenAI(
            model=llm_config["model"],
            api_key=llm_config["api_key"],
            temperature=0.1,
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert software engineer specialized in finding bugs and logic errors in code.

Analyze the provided code for potential bugs including:
- Null pointer/None reference errors
- Array/list index out of bounds
- Off-by-one errors
- Division by zero
- Infinite loops
- Resource leaks (unclosed files, connections)
- Race conditions
- Incorrect exception handling
- Type mismatches
- Logic errors in conditionals
- Uninitialized variables
- Dead code
- Incorrect return values
- Missing error handling
- Incorrect algorithm implementation

For each bug found, provide:
1. Severity (high/medium/low)
2. Title (brief description)
3. Detailed description of the bug
4. Line numbers
5. Code snippet
6. Recommendation for fixing
7. Confidence level (0.0 to 1.0)

Return analysis as JSON array. Focus on real bugs that could cause runtime errors or incorrect behavior."""),
            ("user", """Language: {language}

Code to analyze:
```{language}
{code}
```

Provide bug analysis in JSON format:
[
  {{
    "severity": "high|medium|low",
    "title": "Brief title",
    "description": "Detailed description",
    "line_start": 10,
    "line_end": 15,
    "code_snippet": "buggy code",
    "recommendation": "How to fix",
    "confidence": 0.90
  }}
]""")
        ])
    
    def analyze(self, state: AgentState) -> AgentState:
        """Analyze code for bugs and logic errors."""
        logger.info(f"Bug detector analyzing code (review_id: {state.review_id})")
        
        try:
            # Use LLM to detect bugs
            chain = self.prompt | self.llm
            response = chain.invoke({
                "code": state.code,
                "language": state.language
            })
            
            # Parse LLM response
            issues = self._parse_llm_response(response.content)
            
            # Add to state
            state.bug_issues.extend(issues)
            
            logger.info(f"Bug detector found {len(issues)} potential bugs")
            
        except Exception as e:
            logger.error(f"Bug detector error: {e}")
            state.errors.append(f"Bug detection error: {str(e)}")
        
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
                logger.warning("No JSON array found in bug detector response")
                return issues
            
            data = json.loads(json_match.group())
            
            for item in data:
                # Determine category
                category = IssueCategory.BUG
                title_lower = item.get("title", "").lower()
                if "logic" in title_lower:
                    category = IssueCategory.LOGIC_ERROR
                
                issue = CodeIssue(
                    id=str(uuid.uuid4()),
                    category=category,
                    severity=Severity(item.get("severity", "medium")),
                    title=item.get("title", "Bug"),
                    description=item.get("description", ""),
                    line_start=item.get("line_start"),
                    line_end=item.get("line_end"),
                    code_snippet=item.get("code_snippet"),
                    recommendation=item.get("recommendation"),
                    confidence=float(item.get("confidence", 0.8)),
                    source="bug_detector_agent",
                )
                issues.append(issue)
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse bug detector JSON response: {e}")
        except Exception as e:
            logger.error(f"Error parsing bug detector response: {e}")
        
        return issues


def detect_common_bugs(code: str, language: str) -> List[CodeIssue]:
    """Pattern-based detection of common bugs."""
    import re
    
    issues = []
    
    if language == "python":
        patterns = {
            r"except\s*:": ("Bare except clause", "Use specific exception types", Severity.MEDIUM),
            r"==\s*None": ("Use 'is None' instead of '== None'", "Use identity check for None", Severity.LOW),
            r"!=\s*None": ("Use 'is not None' instead of '!= None'", "Use identity check for None", Severity.LOW),
            r"for\s+\w+\s+in\s+range\(len\([^)]+\)\)": ("Inefficient iteration", "Iterate directly over collection", Severity.LOW),
        }
        
        for pattern, (title, desc, severity) in patterns.items():
            matches = re.finditer(pattern, code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    id=str(uuid.uuid4()),
                    category=IssueCategory.BUG,
                    severity=severity,
                    title=title,
                    description=desc,
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=match.group(),
                    recommendation="Fix the issue as described",
                    confidence=0.7,
                    source="pattern_matcher",
                ))
    
    return issues
