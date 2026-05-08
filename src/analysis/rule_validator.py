"""Rule-based validation for code patterns."""

import re
import uuid
from typing import Dict, List, Tuple

from loguru import logger

from src.agents.models import CodeIssue, IssueCategory, Severity


class RuleValidator:
    """Validates code against predefined rules and patterns."""
    
    def __init__(self):
        """Initialize rule validator."""
        self.rules = self._load_rules()
    
    def validate(self, code: str, language: str) -> List[CodeIssue]:
        """
        Validate code against rules.
        
        Args:
            code: Source code to validate
            language: Programming language
        
        Returns:
            List of issues found
        """
        issues = []
        
        rules_for_language = self.rules.get(language, {})
        
        for rule_name, rule_data in rules_for_language.items():
            pattern = rule_data['pattern']
            category = rule_data['category']
            severity = rule_data['severity']
            title = rule_data['title']
            description = rule_data['description']
            recommendation = rule_data['recommendation']
            
            matches = re.finditer(pattern, code, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                
                issue = CodeIssue(
                    id=str(uuid.uuid4()),
                    category=category,
                    severity=severity,
                    title=title,
                    description=description,
                    line_start=line_num,
                    line_end=line_num,
                    code_snippet=match.group(),
                    recommendation=recommendation,
                    confidence=0.75,
                    source="rule_validator",
                    metadata={"rule": rule_name}
                )
                issues.append(issue)
        
        logger.info(f"Rule validator found {len(issues)} issues for {language}")
        return issues
    
    def _load_rules(self) -> Dict[str, Dict]:
        """Load validation rules."""
        return {
            "python": {
                "hardcoded_password": {
                    "pattern": r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{3,}["\']',
                    "category": IssueCategory.SECURITY,
                    "severity": Severity.CRITICAL,
                    "title": "Hardcoded Password",
                    "description": "Password should not be hardcoded in source code",
                    "recommendation": "Use environment variables or secure configuration management"
                },
                "hardcoded_secret": {
                    "pattern": r'(?:secret|api_key|token|private_key)\s*=\s*["\'][^"\']{10,}["\']',
                    "category": IssueCategory.SECURITY,
                    "severity": Severity.CRITICAL,
                    "title": "Hardcoded Secret",
                    "description": "Secrets should not be hardcoded in source code",
                    "recommendation": "Use environment variables or secret management services"
                },
                "eval_usage": {
                    "pattern": r'\beval\s*\(',
                    "category": IssueCategory.SECURITY,
                    "severity": Severity.HIGH,
                    "title": "Unsafe eval() Usage",
                    "description": "eval() can execute arbitrary code and is a security risk",
                    "recommendation": "Use ast.literal_eval() for safe evaluation or refactor to avoid eval"
                },
                "exec_usage": {
                    "pattern": r'\bexec\s*\(',
                    "category": IssueCategory.SECURITY,
                    "severity": Severity.HIGH,
                    "title": "Unsafe exec() Usage",
                    "description": "exec() can execute arbitrary code and is a security risk",
                    "recommendation": "Refactor to avoid dynamic code execution"
                },
                "pickle_loads": {
                    "pattern": r'pickle\.loads?\s*\(',
                    "category": IssueCategory.SECURITY,
                    "severity": Severity.CRITICAL,
                    "title": "Unsafe Deserialization",
                    "description": "pickle.loads() can execute arbitrary code during deserialization",
                    "recommendation": "Use JSON or other safe serialization formats"
                },
                "sql_string_concat": {
                    "pattern": r'(?:execute|cursor)\s*\([^)]*["\'][^"\']*\+[^)]*["\']',
                    "category": IssueCategory.SECURITY,
                    "severity": Severity.CRITICAL,
                    "title": "SQL Injection Risk",
                    "description": "SQL query constructed using string concatenation",
                    "recommendation": "Use parameterized queries or ORM"
                },
                "shell_injection": {
                    "pattern": r'(?:os\.system|subprocess\.(?:call|run|Popen))\s*\([^)]*shell\s*=\s*True',
                    "category": IssueCategory.SECURITY,
                    "severity": Severity.HIGH,
                    "title": "Shell Injection Risk",
                    "description": "Using shell=True can lead to command injection",
                    "recommendation": "Avoid shell=True or properly sanitize input"
                },
                "bare_except": {
                    "pattern": r'except\s*:',
                    "category": IssueCategory.BUG,
                    "severity": Severity.MEDIUM,
                    "title": "Bare Except Clause",
                    "description": "Catching all exceptions can hide bugs",
                    "recommendation": "Catch specific exception types"
                },
                "print_debug": {
                    "pattern": r'^\s*print\s*\(',
                    "category": IssueCategory.MAINTAINABILITY,
                    "severity": Severity.LOW,
                    "title": "Debug Print Statement",
                    "description": "Print statements should not be used in production code",
                    "recommendation": "Use proper logging instead of print()"
                },
                "todo_comment": {
                    "pattern": r'#\s*TODO:',
                    "category": IssueCategory.MAINTAINABILITY,
                    "severity": Severity.INFO,
                    "title": "TODO Comment",
                    "description": "Unresolved TODO comment",
                    "recommendation": "Complete or track TODO items"
                },
                "fixme_comment": {
                    "pattern": r'#\s*FIXME:',
                    "category": IssueCategory.BUG,
                    "severity": Severity.MEDIUM,
                    "title": "FIXME Comment",
                    "description": "Code marked for fixing",
                    "recommendation": "Address FIXME items before production"
                },
                "comparison_to_none": {
                    "pattern": r'(?:==|!=)\s*None',
                    "category": IssueCategory.STYLE,
                    "severity": Severity.LOW,
                    "title": "Incorrect None Comparison",
                    "description": "Should use 'is None' or 'is not None'",
                    "recommendation": "Use 'is None' instead of '== None'"
                },
                "mutable_default_arg": {
                    "pattern": r'def\s+\w+\s*\([^)]*=\s*(?:\[\]|\{\})',
                    "category": IssueCategory.BUG,
                    "severity": Severity.HIGH,
                    "title": "Mutable Default Argument",
                    "description": "Mutable default arguments can lead to unexpected behavior",
                    "recommendation": "Use None as default and create mutable objects inside function"
                },
            },
            "javascript": {
                "eval_usage": {
                    "pattern": r'\beval\s*\(',
                    "category": IssueCategory.SECURITY,
                    "severity": Severity.HIGH,
                    "title": "Unsafe eval() Usage",
                    "description": "eval() can execute arbitrary code",
                    "recommendation": "Avoid eval() or use safer alternatives"
                },
                "console_log": {
                    "pattern": r'console\.log\s*\(',
                    "category": IssueCategory.MAINTAINABILITY,
                    "severity": Severity.LOW,
                    "title": "Console Log Statement",
                    "description": "Console logs should not be in production code",
                    "recommendation": "Remove console.log or use proper logging"
                },
                "var_keyword": {
                    "pattern": r'\bvar\s+\w+',
                    "category": IssueCategory.STYLE,
                    "severity": Severity.LOW,
                    "title": "Use of 'var' Keyword",
                    "description": "Use 'let' or 'const' instead of 'var'",
                    "recommendation": "Replace 'var' with 'let' or 'const'"
                },
            }
        }
    
    def add_custom_rule(
        self,
        language: str,
        name: str,
        pattern: str,
        category: IssueCategory,
        severity: Severity,
        title: str,
        description: str,
        recommendation: str
    ) -> None:
        """Add a custom validation rule."""
        if language not in self.rules:
            self.rules[language] = {}
        
        self.rules[language][name] = {
            "pattern": pattern,
            "category": category,
            "severity": severity,
            "title": title,
            "description": description,
            "recommendation": recommendation,
        }
        
        logger.info(f"Added custom rule '{name}' for {language}")
