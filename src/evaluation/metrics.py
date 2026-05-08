"""Evaluation metrics for code review system."""

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
from loguru import logger

from src.agents.models import CodeIssue, IssueCategory, Severity


@dataclass
class ConfusionMatrix:
    """Confusion matrix for binary classification."""
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    
    @property
    def total(self) -> int:
        """Total number of predictions."""
        return self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
    
    @property
    def precision(self) -> float:
        """Calculate precision (TP / (TP + FP))."""
        denominator = self.true_positives + self.false_positives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator
    
    @property
    def recall(self) -> float:
        """Calculate recall (TP / (TP + FN))."""
        denominator = self.true_positives + self.false_negatives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator
    
    @property
    def f1_score(self) -> float:
        """Calculate F1 score (harmonic mean of precision and recall)."""
        p = self.precision
        r = self.recall
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy ((TP + TN) / Total)."""
        if self.total == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / self.total
    
    @property
    def specificity(self) -> float:
        """Calculate specificity (TN / (TN + FP))."""
        denominator = self.true_negatives + self.false_positives
        if denominator == 0:
            return 0.0
        return self.true_negatives / denominator
    
    @property
    def false_positive_rate(self) -> float:
        """Calculate false positive rate (FP / (FP + TN))."""
        return 1.0 - self.specificity
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "accuracy": self.accuracy,
            "specificity": self.specificity,
            "false_positive_rate": self.false_positive_rate,
        }


@dataclass
class EvaluationMetrics:
    """Comprehensive evaluation metrics."""
    
    # Overall metrics
    confusion_matrix: ConfusionMatrix
    
    # Per-category metrics
    category_metrics: Dict[str, ConfusionMatrix]
    
    # Per-severity metrics
    severity_metrics: Dict[str, ConfusionMatrix]
    
    # Additional metrics
    hallucination_rate: float  # False positive rate
    detection_coverage: float  # Recall
    average_confidence: float
    
    def summary(self) -> Dict[str, any]:
        """Get metrics summary."""
        return {
            "overall": self.confusion_matrix.to_dict(),
            "hallucination_rate": self.hallucination_rate,
            "detection_coverage": self.detection_coverage,
            "average_confidence": self.average_confidence,
            "precision": self.confusion_matrix.precision,
            "recall": self.confusion_matrix.recall,
            "f1_score": self.confusion_matrix.f1_score,
        }
    
    def detailed_report(self) -> Dict[str, any]:
        """Get detailed evaluation report."""
        return {
            "overall_metrics": self.confusion_matrix.to_dict(),
            "category_breakdown": {
                cat: metrics.to_dict()
                for cat, metrics in self.category_metrics.items()
            },
            "severity_breakdown": {
                sev: metrics.to_dict()
                for sev, metrics in self.severity_metrics.items()
            },
            "hallucination_rate": self.hallucination_rate,
            "detection_coverage": self.detection_coverage,
            "average_confidence": self.average_confidence,
        }


class MetricsCalculator:
    """Calculates evaluation metrics for code review system."""
    
    @staticmethod
    def calculate_metrics(
        predicted_issues: List[CodeIssue],
        ground_truth_issues: List[CodeIssue],
        match_threshold: float = 0.8
    ) -> EvaluationMetrics:
        """
        Calculate evaluation metrics.
        
        Args:
            predicted_issues: Issues detected by the system
            ground_truth_issues: Known issues (ground truth)
            match_threshold: Threshold for matching issues
        
        Returns:
            EvaluationMetrics
        """
        # Match predicted issues to ground truth
        matches = MetricsCalculator._match_issues(
            predicted_issues,
            ground_truth_issues,
            match_threshold
        )
        
        # Calculate overall confusion matrix
        overall_cm = ConfusionMatrix()
        overall_cm.true_positives = len(matches["true_positives"])
        overall_cm.false_positives = len(matches["false_positives"])
        overall_cm.false_negatives = len(matches["false_negatives"])
        overall_cm.true_negatives = 0  # Not applicable for issue detection
        
        # Calculate per-category metrics
        category_metrics = MetricsCalculator._calculate_category_metrics(
            predicted_issues,
            ground_truth_issues,
            matches
        )
        
        # Calculate per-severity metrics
        severity_metrics = MetricsCalculator._calculate_severity_metrics(
            predicted_issues,
            ground_truth_issues,
            matches
        )
        
        # Calculate additional metrics
        hallucination_rate = overall_cm.false_positive_rate
        detection_coverage = overall_cm.recall
        
        avg_confidence = (
            sum(issue.confidence for issue in predicted_issues) / len(predicted_issues)
            if predicted_issues else 0.0
        )
        
        return EvaluationMetrics(
            confusion_matrix=overall_cm,
            category_metrics=category_metrics,
            severity_metrics=severity_metrics,
            hallucination_rate=hallucination_rate,
            detection_coverage=detection_coverage,
            average_confidence=avg_confidence,
        )
    
    @staticmethod
    def _match_issues(
        predicted: List[CodeIssue],
        ground_truth: List[CodeIssue],
        threshold: float
    ) -> Dict[str, List[CodeIssue]]:
        """Match predicted issues to ground truth."""
        true_positives = []
        false_positives = []
        false_negatives = []
        
        matched_gt = set()
        
        for pred in predicted:
            best_match = None
            best_score = 0.0
            
            for i, gt in enumerate(ground_truth):
                if i in matched_gt:
                    continue
                
                score = MetricsCalculator._similarity_score(pred, gt)
                if score > best_score:
                    best_score = score
                    best_match = i
            
            if best_score >= threshold and best_match is not None:
                true_positives.append(pred)
                matched_gt.add(best_match)
            else:
                false_positives.append(pred)
        
        # Unmatched ground truth issues are false negatives
        for i, gt in enumerate(ground_truth):
            if i not in matched_gt:
                false_negatives.append(gt)
        
        return {
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
        }
    
    @staticmethod
    def _similarity_score(issue1: CodeIssue, issue2: CodeIssue) -> float:
        """Calculate similarity score between two issues."""
        score = 0.0
        
        # Category match (30%)
        if issue1.category == issue2.category:
            score += 0.3
        
        # Severity match (20%)
        if issue1.severity == issue2.severity:
            score += 0.2
        
        # Line number proximity (30%)
        if issue1.line_start and issue2.line_start:
            line_diff = abs(issue1.line_start - issue2.line_start)
            if line_diff == 0:
                score += 0.3
            elif line_diff <= 2:
                score += 0.2
            elif line_diff <= 5:
                score += 0.1
        
        # Title similarity (20%)
        if issue1.title and issue2.title:
            common_words = set(issue1.title.lower().split()) & set(issue2.title.lower().split())
            if common_words:
                score += 0.2 * (len(common_words) / max(len(issue1.title.split()), len(issue2.title.split())))
        
        return min(score, 1.0)
    
    @staticmethod
    def _calculate_category_metrics(
        predicted: List[CodeIssue],
        ground_truth: List[CodeIssue],
        matches: Dict[str, List[CodeIssue]]
    ) -> Dict[str, ConfusionMatrix]:
        """Calculate metrics per category."""
        categories = set(
            [issue.category for issue in predicted + ground_truth]
        )
        
        category_metrics = {}
        
        for category in categories:
            cm = ConfusionMatrix()
            
            cm.true_positives = sum(
                1 for issue in matches["true_positives"]
                if issue.category == category
            )
            
            cm.false_positives = sum(
                1 for issue in matches["false_positives"]
                if issue.category == category
            )
            
            cm.false_negatives = sum(
                1 for issue in matches["false_negatives"]
                if issue.category == category
            )
            
            category_metrics[category.value] = cm
        
        return category_metrics
    
    @staticmethod
    def _calculate_severity_metrics(
        predicted: List[CodeIssue],
        ground_truth: List[CodeIssue],
        matches: Dict[str, List[CodeIssue]]
    ) -> Dict[str, ConfusionMatrix]:
        """Calculate metrics per severity."""
        severities = set(
            [issue.severity for issue in predicted + ground_truth]
        )
        
        severity_metrics = {}
        
        for severity in severities:
            cm = ConfusionMatrix()
            
            cm.true_positives = sum(
                1 for issue in matches["true_positives"]
                if issue.severity == severity
            )
            
            cm.false_positives = sum(
                1 for issue in matches["false_positives"]
                if issue.severity == severity
            )
            
            cm.false_negatives = sum(
                1 for issue in matches["false_negatives"]
                if issue.severity == severity
            )
            
            severity_metrics[severity.value] = cm
        
        return severity_metrics


def print_metrics_report(metrics: EvaluationMetrics) -> None:
    """Print a formatted metrics report."""
    print("\n" + "="*60)
    print("CODE REVIEW EVALUATION REPORT")
    print("="*60)
    
    print("\nOVERALL METRICS:")
    print(f"  Precision:           {metrics.confusion_matrix.precision:.3f}")
    print(f"  Recall:              {metrics.confusion_matrix.recall:.3f}")
    print(f"  F1 Score:            {metrics.confusion_matrix.f1_score:.3f}")
    print(f"  Hallucination Rate:  {metrics.hallucination_rate:.3f}")
    print(f"  Detection Coverage:  {metrics.detection_coverage:.3f}")
    print(f"  Average Confidence:  {metrics.average_confidence:.3f}")
    
    print("\nCONFUSION MATRIX:")
    cm = metrics.confusion_matrix
    print(f"  True Positives:      {cm.true_positives}")
    print(f"  False Positives:     {cm.false_positives}")
    print(f"  False Negatives:     {cm.false_negatives}")
    
    print("\nCATEGORY BREAKDOWN:")
    for cat, cat_cm in metrics.category_metrics.items():
        print(f"\n  {cat.upper()}:")
        print(f"    Precision: {cat_cm.precision:.3f}")
        print(f"    Recall:    {cat_cm.recall:.3f}")
        print(f"    F1 Score:  {cat_cm.f1_score:.3f}")
    
    print("\n" + "="*60)
