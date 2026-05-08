"""Evaluation framework and metrics."""

from src.evaluation.benchmark import Benchmark, run_quick_test
from src.evaluation.confusion_matrix import (
    create_evaluation_report,
    plot_category_breakdown,
    plot_confusion_matrix,
    plot_metrics_comparison,
)
from src.evaluation.metrics import (
    ConfusionMatrix,
    EvaluationMetrics,
    MetricsCalculator,
    print_metrics_report,
)

__all__ = [
    "Benchmark",
    "ConfusionMatrix",
    "EvaluationMetrics",
    "MetricsCalculator",
    "create_evaluation_report",
    "plot_category_breakdown",
    "plot_confusion_matrix",
    "plot_metrics_comparison",
    "print_metrics_report",
    "run_quick_test",
]
