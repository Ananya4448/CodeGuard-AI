"""Static analysis tools integration."""

import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

from loguru import logger

from src.agents.models import CodeIssue, IssueCategory, Severity
from src.core.config import Config


class StaticAnalyzer:
    """Integrates multiple static analysis tools."""
    
    def __init__(self, config: Config):
        """Initialize static analyzer."""
        self.config = config
    
    def analyze(self, code: str, language: str) -> List[CodeIssue]:
        """
        Run static analysis on code.
        
        Args:
            code: Source code to analyze
            language: Programming language
        
        Returns:
            List of detected issues
        """
        issues = []
        
        if language == "python":
            if self.config.pylint_enabled:
                issues.extend(self._run_pylint(code))
            
            if self.config.flake8_enabled:
                issues.extend(self._run_flake8(code))
            
            if self.config.bandit_enabled:
                issues.extend(self._run_bandit(code))
            
            if self.config.mypy_enabled:
                issues.extend(self._run_mypy(code))
        
        logger.info(f"Static analysis found {len(issues)} issues")
        return issues
    
    def _run_pylint(self, code: str) -> List[CodeIssue]:
        """Run Pylint analysis."""
        issues = []
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['pylint', '--output-format=json', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse Pylint JSON output
            import json
            if result.stdout:
                pylint_issues = json.loads(result.stdout)
                
                for item in pylint_issues:
                    severity = self._map_pylint_severity(item.get('type', 'info'))
                    category = self._map_pylint_category(item.get('symbol', ''))
                    
                    issue = CodeIssue(
                        id=str(uuid.uuid4()),
                        category=category,
                        severity=severity,
                        title=item.get('symbol', 'Pylint Issue'),
                        description=item.get('message', ''),
                        line_start=item.get('line'),
                        line_end=item.get('endLine', item.get('line')),
                        code_snippet=None,
                        recommendation=f"Pylint: {item.get('message-id', '')}",
                        confidence=0.85,
                        source="pylint",
                        metadata={"message_id": item.get('message-id')}
                    )
                    issues.append(issue)
            
            # Clean up
            Path(temp_file).unlink()
        
        except subprocess.TimeoutExpired:
            logger.warning("Pylint analysis timed out")
        except Exception as e:
            logger.error(f"Error running Pylint: {e}")
        
        return issues
    
    def _run_flake8(self, code: str) -> List[CodeIssue]:
        """Run Flake8 analysis."""
        issues = []
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['flake8', '--format=json', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Flake8 with json format plugin
            # Fallback to parsing standard output
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    
                    # Format: filename:line:col: code message
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        line_num = int(parts[1])
                        code_msg = parts[3].strip()
                        
                        # Extract error code
                        error_code = code_msg.split()[0] if code_msg else "E"
                        
                        severity = self._map_flake8_severity(error_code)
                        
                        issue = CodeIssue(
                            id=str(uuid.uuid4()),
                            category=IssueCategory.STYLE,
                            severity=severity,
                            title=f"Flake8: {error_code}",
                            description=code_msg,
                            line_start=line_num,
                            line_end=line_num,
                            code_snippet=None,
                            recommendation="Follow PEP 8 style guidelines",
                            confidence=0.9,
                            source="flake8",
                            metadata={"error_code": error_code}
                        )
                        issues.append(issue)
            
            # Clean up
            Path(temp_file).unlink()
        
        except subprocess.TimeoutExpired:
            logger.warning("Flake8 analysis timed out")
        except Exception as e:
            logger.error(f"Error running Flake8: {e}")
        
        return issues
    
    def _run_bandit(self, code: str) -> List[CodeIssue]:
        """Run Bandit security analysis."""
        issues = []
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['bandit', '-f', 'json', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse Bandit JSON output
            import json
            if result.stdout:
                bandit_output = json.loads(result.stdout)
                
                for item in bandit_output.get('results', []):
                    severity = self._map_bandit_severity(item.get('issue_severity', 'LOW'))
                    
                    issue = CodeIssue(
                        id=str(uuid.uuid4()),
                        category=IssueCategory.SECURITY,
                        severity=severity,
                        title=item.get('test_id', 'Security Issue'),
                        description=item.get('issue_text', ''),
                        line_start=item.get('line_number'),
                        line_end=item.get('line_number'),
                        code_snippet=item.get('code'),
                        recommendation=item.get('more_info', ''),
                        confidence=self._map_bandit_confidence(item.get('issue_confidence', 'MEDIUM')),
                        source="bandit",
                        metadata={
                            "test_id": item.get('test_id'),
                            "cwe": item.get('cwe', {})
                        }
                    )
                    issues.append(issue)
            
            # Clean up
            Path(temp_file).unlink()
        
        except subprocess.TimeoutExpired:
            logger.warning("Bandit analysis timed out")
        except Exception as e:
            logger.error(f"Error running Bandit: {e}")
        
        return issues
    
    def _run_mypy(self, code: str) -> List[CodeIssue]:
        """Run MyPy type checking."""
        issues = []
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['mypy', '--no-error-summary', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse MyPy output
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if not line or ':' not in line:
                        continue
                    
                    # Format: filename:line: error: message
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        line_num = int(parts[1])
                        message = parts[3].strip()
                        
                        issue = CodeIssue(
                            id=str(uuid.uuid4()),
                            category=IssueCategory.BUG,
                            severity=Severity.MEDIUM,
                            title="Type Error",
                            description=message,
                            line_start=line_num,
                            line_end=line_num,
                            code_snippet=None,
                            recommendation="Add proper type annotations",
                            confidence=0.8,
                            source="mypy",
                        )
                        issues.append(issue)
            
            # Clean up
            Path(temp_file).unlink()
        
        except subprocess.TimeoutExpired:
            logger.warning("MyPy analysis timed out")
        except Exception as e:
            logger.error(f"Error running MyPy: {e}")
        
        return issues
    
    @staticmethod
    def _map_pylint_severity(pylint_type: str) -> Severity:
        """Map Pylint message type to Severity."""
        mapping = {
            'error': Severity.HIGH,
            'warning': Severity.MEDIUM,
            'refactor': Severity.LOW,
            'convention': Severity.LOW,
            'info': Severity.INFO,
        }
        return mapping.get(pylint_type.lower(), Severity.INFO)
    
    @staticmethod
    def _map_pylint_category(symbol: str) -> IssueCategory:
        """Map Pylint symbol to IssueCategory."""
        if 'security' in symbol.lower():
            return IssueCategory.SECURITY
        if any(x in symbol.lower() for x in ['error', 'exception', 'undefined']):
            return IssueCategory.BUG
        if 'complex' in symbol.lower():
            return IssueCategory.COMPLEXITY
        return IssueCategory.STYLE
    
    @staticmethod
    def _map_flake8_severity(error_code: str) -> Severity:
        """Map Flake8 error code to Severity."""
        if error_code.startswith('E9') or error_code.startswith('F'):
            return Severity.HIGH
        if error_code.startswith('E') or error_code.startswith('W'):
            return Severity.LOW
        return Severity.INFO
    
    @staticmethod
    def _map_bandit_severity(bandit_severity: str) -> Severity:
        """Map Bandit severity to Severity."""
        mapping = {
            'HIGH': Severity.CRITICAL,
            'MEDIUM': Severity.MEDIUM,
            'LOW': Severity.LOW,
        }
        return mapping.get(bandit_severity.upper(), Severity.MEDIUM)
    
    @staticmethod
    def _map_bandit_confidence(bandit_confidence: str) -> float:
        """Map Bandit confidence to float."""
        mapping = {
            'HIGH': 0.9,
            'MEDIUM': 0.7,
            'LOW': 0.5,
        }
        return mapping.get(bandit_confidence.upper(), 0.7)
