"""Anti-pattern detection and common code smells."""

from dataclasses import dataclass
from typing import List, Optional

import ast

from loguru import logger


@dataclass
class AntiPattern:
    """Represents an anti-pattern detection."""
    name: str
    description: str
    line_number: int
    severity: str
    recommendation: str


class AntiPatternDetector:
    """Detects anti-patterns and code smells in Python code."""
    
    def __init__(self):
        """Initialize anti-pattern detector."""
        pass
    
    def detect(self, code: str, language: str = "python") -> List[AntiPattern]:
        """
        Detect anti-patterns in code.
        
        Args:
            code: Source code to analyze
            language: Programming language
        
        Returns:
            List of detected anti-patterns
        """
        if language != "python":
            return []
        
        try:
            tree = ast.parse(code)
            patterns = []
            
            # Detect various anti-patterns
            patterns.extend(self._detect_god_class(tree))
            patterns.extend(self._detect_long_methods(tree))
            patterns.extend(self._detect_deep_nesting(tree, code))
            patterns.extend(self._detect_too_many_parameters(tree))
            patterns.extend(self._detect_empty_except(tree))
            
            logger.info(f"Detected {len(patterns)} anti-patterns")
            return patterns
        
        except SyntaxError as e:
            logger.warning(f"Syntax error in code, cannot detect anti-patterns: {e}")
            return []
        except Exception as e:
            logger.error(f"Error detecting anti-patterns: {e}")
            return []
    
    def _detect_god_class(self, tree: ast.AST) -> List[AntiPattern]:
        """Detect god classes (classes with too many methods)."""
        patterns = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                
                if len(methods) > 20:
                    patterns.append(AntiPattern(
                        name="God Class",
                        description=f"Class '{node.name}' has {len(methods)} methods. Consider splitting into smaller, focused classes.",
                        line_number=node.lineno,
                        severity="medium",
                        recommendation="Apply Single Responsibility Principle and extract related methods into separate classes"
                    ))
        
        return patterns
    
    def _detect_long_methods(self, tree: ast.AST) -> List[AntiPattern]:
        """Detect long methods (functions with too many lines)."""
        patterns = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Calculate function length
                if hasattr(node, 'end_lineno'):
                    length = node.end_lineno - node.lineno
                    
                    if length > 50:
                        patterns.append(AntiPattern(
                            name="Long Method",
                            description=f"Function '{node.name}' has {length} lines. Long functions are hard to understand and maintain.",
                            line_number=node.lineno,
                            severity="medium",
                            recommendation="Extract smaller functions from this large function"
                        ))
        
        return patterns
    
    def _detect_deep_nesting(self, tree: ast.AST, code: str) -> List[AntiPattern]:
        """Detect deep nesting (too many nested blocks)."""
        patterns = []
        
        class NestingVisitor(ast.NodeVisitor):
            def __init__(self):
                self.max_depth = 0
                self.current_depth = 0
                self.depth_locations = []
            
            def visit_If(self, node):
                self.current_depth += 1
                if self.current_depth > 4:
                    self.depth_locations.append((node.lineno, self.current_depth))
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1
            
            visit_For = visit_If
            visit_While = visit_If
            visit_With = visit_If
        
        visitor = NestingVisitor()
        visitor.visit(tree)
        
        for line_no, depth in visitor.depth_locations:
            patterns.append(AntiPattern(
                name="Deep Nesting",
                description=f"Code is nested {depth} levels deep. Deep nesting makes code hard to read.",
                line_number=line_no,
                severity="medium",
                recommendation="Extract nested logic into separate functions or use early returns"
            ))
        
        return patterns
    
    def _detect_too_many_parameters(self, tree: ast.AST) -> List[AntiPattern]:
        """Detect functions with too many parameters."""
        patterns = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                param_count = len(node.args.args)
                
                if param_count > 5:
                    patterns.append(AntiPattern(
                        name="Too Many Parameters",
                        description=f"Function '{node.name}' has {param_count} parameters. Functions with many parameters are hard to use.",
                        line_number=node.lineno,
                        severity="low",
                        recommendation="Group related parameters into objects or use keyword arguments"
                    ))
        
        return patterns
    
    def _detect_empty_except(self, tree: ast.AST) -> List[AntiPattern]:
        """Detect empty except blocks."""
        patterns = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Check if except block is empty (only contains pass)
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    patterns.append(AntiPattern(
                        name="Empty Except Block",
                        description="Empty except block silently swallows errors, making debugging difficult.",
                        line_number=node.lineno,
                        severity="high",
                        recommendation="Either handle the exception properly or log it"
                    ))
        
        return patterns


class ComplexityAnalyzer:
    """Analyzes code complexity metrics."""
    
    @staticmethod
    def calculate_cyclomatic_complexity(code: str) -> int:
        """Calculate cyclomatic complexity using radon."""
        try:
            from radon.complexity import cc_visit
            
            results = cc_visit(code)
            if not results:
                return 1
            
            # Return maximum complexity
            return max(func.complexity for func in results)
        
        except Exception as e:
            logger.warning(f"Error calculating complexity: {e}")
            return 0
    
    @staticmethod
    def calculate_maintainability_index(code: str) -> float:
        """Calculate maintainability index using radon."""
        try:
            from radon.metrics import mi_visit
            
            result = mi_visit(code, True)
            return result if result else 0.0
        
        except Exception as e:
            logger.warning(f"Error calculating maintainability index: {e}")
            return 0.0
    
    @staticmethod
    def calculate_halstead_metrics(code: str) -> dict:
        """Calculate Halstead complexity metrics."""
        try:
            from radon.metrics import h_visit
            
            results = h_visit(code)
            if not results:
                return {}
            
            total = results[0]  # Total for entire module
            return {
                "volume": total.volume,
                "difficulty": total.difficulty,
                "effort": total.effort,
            }
        
        except Exception as e:
            logger.warning(f"Error calculating Halstead metrics: {e}")
            return {}
