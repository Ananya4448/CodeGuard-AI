"""Benchmarking and testing framework."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from src.agents.models import CodeIssue, IssueCategory, ReviewResult, Severity
from src.agents.orchestrator import CodeReviewOrchestrator
from src.core.config import Config
from src.evaluation.metrics import EvaluationMetrics, MetricsCalculator, print_metrics_report


class Benchmark:
    """Benchmark the code review system."""
    
    def __init__(self, config: Config, dataset_path: Optional[str] = None):
        """Initialize benchmark."""
        self.config = config
        self.orchestrator = CodeReviewOrchestrator(config)
        self.dataset_path = dataset_path or config.evaluation_dataset_path
    
    def run(self) -> EvaluationMetrics:
        """Run benchmark evaluation."""
        logger.info("Starting benchmark evaluation")
        
        # Load dataset
        dataset = self._load_dataset()
        
        if not dataset:
            logger.error("No benchmark dataset found")
            raise ValueError("Benchmark dataset is required")
        
        all_predicted = []
        all_ground_truth = []
        
        # Run review on each sample
        for i, sample in enumerate(dataset):
            logger.info(f"Processing sample {i+1}/{len(dataset)}")
            
            code = sample["code"]
            language = sample["language"]
            ground_truth = sample["issues"]
            
            # Run review
            result = self.orchestrator.review_code(code, language)
            
            # Collect results
            all_predicted.extend(result.issues)
            all_ground_truth.extend(self._parse_ground_truth(ground_truth))
        
        # Calculate metrics
        metrics = MetricsCalculator.calculate_metrics(
            all_predicted,
            all_ground_truth,
            match_threshold=0.7
        )
        
        # Print report
        print_metrics_report(metrics)
        
        # Save results
        self._save_results(metrics)
        
        logger.info("Benchmark evaluation completed")
        return metrics
    
    def _load_dataset(self) -> List[Dict]:
        """Load benchmark dataset."""
        dataset_path = Path(self.dataset_path)
        
        if not dataset_path.exists():
            logger.warning(f"Dataset not found at {dataset_path}, creating sample dataset")
            return self._create_sample_dataset()
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _create_sample_dataset(self) -> List[Dict]:
        """Create sample dataset for testing."""
        return [
            {
                "code": """
import pickle
import os

def process_data(user_input):
    # Load data from pickle
    data = pickle.loads(user_input)
    
    # Execute user command
    result = eval(user_input)
    
    # Hardcoded password
    password = "admin123"
    
    return result
""",
                "language": "python",
                "issues": [
                    {
                        "category": "security",
                        "severity": "critical",
                        "title": "Unsafe Deserialization",
                        "line_start": 6,
                    },
                    {
                        "category": "security",
                        "severity": "high",
                        "title": "Unsafe eval() Usage",
                        "line_start": 9,
                    },
                    {
                        "category": "security",
                        "severity": "critical",
                        "title": "Hardcoded Password",
                        "line_start": 12,
                    }
                ]
            },
            {
                "code": """
def calculate_average(numbers):
    total = 0
    for i in range(len(numbers)):
        total += numbers[i]
    return total / len(numbers)

def risky_function():
    try:
        dangerous_operation()
    except:
        pass
""",
                "language": "python",
                "issues": [
                    {
                        "category": "style",
                        "severity": "low",
                        "title": "Inefficient iteration",
                        "line_start": 3,
                    },
                    {
                        "category": "bug",
                        "severity": "medium",
                        "title": "Bare Except Clause",
                        "line_start": 10,
                    }
                ]
            }
        ]
    
    def _parse_ground_truth(self, ground_truth: List[Dict]) -> List[CodeIssue]:
        """Parse ground truth issues from dataset."""
        issues = []
        
        for item in ground_truth:
            try:
                issue = CodeIssue(
                    id=f"gt_{len(issues)}",
                    category=IssueCategory(item["category"]),
                    severity=Severity(item["severity"]),
                    title=item["title"],
                    description=item.get("description", ""),
                    line_start=item.get("line_start"),
                    line_end=item.get("line_end", item.get("line_start")),
                    code_snippet=item.get("code_snippet"),
                    recommendation=item.get("recommendation"),
                    confidence=1.0,  # Ground truth has 100% confidence
                    source="ground_truth",
                )
                issues.append(issue)
            except Exception as e:
                logger.warning(f"Error parsing ground truth issue: {e}")
        
        return issues
    
    def _save_results(self, metrics: EvaluationMetrics) -> None:
        """Save benchmark results."""
        results_dir = Path("evaluation_results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"benchmark_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(metrics.detailed_report(), f, indent=2)
        
        logger.info(f"Results saved to {results_file}")


def run_quick_test(config: Optional[Config] = None) -> None:
    """Run a quick test of the system."""
    if config is None:
        config = Config.from_env()
    
    orchestrator = CodeReviewOrchestrator(config)
    
    test_code = """
def unsafe_function(user_input):
    # Security issues
    result = eval(user_input)
    password = "hardcoded123"
    
    # Bug
    try:
        risky_operation()
    except:
        pass
    
    return result
"""
    
    print("\n" + "="*60)
    print("QUICK TEST - Code Review System")
    print("="*60)
    
    result = orchestrator.review_code(test_code, "python")
    
    print(f"\nQuality Score: {result.quality_metrics.overall_score}/100")
    print(f"Issues Found: {len(result.issues)}")
    print(f"Refactorings Suggested: {len(result.refactorings)}")
    
    print("\nISSUES:")
    for issue in result.issues:
        print(f"  [{issue.severity.value.upper()}] {issue.title}")
        print(f"    Line {issue.line_start}: {issue.description}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    # Run quick test
    run_quick_test()
