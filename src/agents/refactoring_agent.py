"""Refactoring agent for code optimization suggestions."""

import uuid
from typing import List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from loguru import logger

from src.agents.models import AgentState, RefactoringTask, Severity
from src.core.config import Config


class RefactoringAgent:
    """Agent specialized in suggesting code refactorings."""
    
    def __init__(self, config: Config):
        """Initialize refactoring agent."""
        self.config = config
        llm_config = config.get_llm_config()
        
        self.llm = ChatOpenAI(
            model=llm_config["model"],
            api_key=llm_config["api_key"],
            temperature=0.2,  # Slightly higher for creative refactoring
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert software architect specialized in code refactoring and optimization.

Analyze the provided code and suggest refactorings to improve:
- Code readability and clarity
- Maintainability
- Performance
- Design patterns usage
- DRY (Don't Repeat Yourself) principle
- SOLID principles
- Separation of concerns
- Error handling
- Code structure and organization
- Variable/function naming
- Complexity reduction

For each refactoring suggestion, provide:
1. Title (what to refactor)
2. Description (why and how)
3. Original code snippet
4. Refactored code snippet
5. Benefits of the refactoring
6. Priority (high/medium/low)
7. Line numbers (if applicable)
8. Confidence level (0.0 to 1.0)

Return suggestions as JSON array. Focus on meaningful refactorings that add real value."""),
            ("user", """Language: {language}

Code to analyze:
```{language}
{code}
```

Provide refactoring suggestions in JSON format:
[
  {{
    "title": "Refactoring title",
    "description": "Why and how to refactor",
    "original_code": "original code snippet",
    "refactored_code": "improved code snippet",
    "benefits": ["benefit 1", "benefit 2"],
    "priority": "high|medium|low",
    "line_start": 10,
    "line_end": 20,
    "confidence": 0.90
  }}
]""")
        ])
    
    def analyze(self, state: AgentState) -> AgentState:
        """Generate refactoring suggestions."""
        logger.info(f"Refactoring agent analyzing code (review_id: {state.review_id})")
        
        try:
            # Use LLM to suggest refactorings
            chain = self.prompt | self.llm
            response = chain.invoke({
                "code": state.code,
                "language": state.language
            })
            
            # Parse LLM response
            refactorings = self._parse_llm_response(response.content)
            
            # Add to state
            state.refactorings.extend(refactorings)
            
            logger.info(f"Refactoring agent suggested {len(refactorings)} refactorings")
            
        except Exception as e:
            logger.error(f"Refactoring agent error: {e}")
            state.errors.append(f"Refactoring analysis error: {str(e)}")
        
        return state
    
    def _parse_llm_response(self, response_text: str) -> List[RefactoringTask]:
        """Parse LLM response into RefactoringTask objects."""
        import json
        import re
        
        refactorings = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                logger.warning("No JSON array found in refactoring agent response")
                return refactorings
            
            data = json.loads(json_match.group())
            
            for item in data:
                priority_map = {
                    "high": Severity.HIGH,
                    "medium": Severity.MEDIUM,
                    "low": Severity.LOW,
                }
                
                refactoring = RefactoringTask(
                    id=str(uuid.uuid4()),
                    title=item.get("title", "Refactoring suggestion"),
                    description=item.get("description", ""),
                    original_code=item.get("original_code", ""),
                    refactored_code=item.get("refactored_code", ""),
                    benefits=item.get("benefits", []),
                    line_start=item.get("line_start"),
                    line_end=item.get("line_end"),
                    priority=priority_map.get(item.get("priority", "medium"), Severity.MEDIUM),
                    confidence=float(item.get("confidence", 0.8)),
                )
                refactorings.append(refactoring)
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse refactoring agent JSON response: {e}")
        except Exception as e:
            logger.error(f"Error parsing refactoring agent response: {e}")
        
        return refactorings


def suggest_basic_refactorings(code: str, language: str) -> List[RefactoringTask]:
    """Pattern-based basic refactoring suggestions."""
    import re
    
    refactorings = []
    
    if language == "python":
        # Check for long functions
        function_pattern = r'def\s+(\w+)\s*\([^)]*\):\s*\n((?:    .*\n)*)'
        matches = re.finditer(function_pattern, code)
        
        for match in matches:
            func_name = match.group(1)
            func_body = match.group(2)
            lines = func_body.strip().split('\n')
            
            if len(lines) > 50:
                line_num = code[:match.start()].count('\n') + 1
                refactorings.append(RefactoringTask(
                    id=str(uuid.uuid4()),
                    title=f"Break down long function '{func_name}'",
                    description=f"Function {func_name} has {len(lines)} lines. Consider breaking it into smaller functions.",
                    original_code=match.group(0),
                    refactored_code="# Break into smaller, focused functions\n# Extract logical sections into separate methods",
                    benefits=[
                        "Improved readability",
                        "Easier testing",
                        "Better maintainability"
                    ],
                    line_start=line_num,
                    line_end=line_num + len(lines),
                    priority=Severity.MEDIUM,
                    confidence=0.9,
                ))
    
    return refactorings
