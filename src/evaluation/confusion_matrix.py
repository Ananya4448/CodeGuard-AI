"""Confusion matrix visualization."""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from loguru import logger

from src.evaluation.metrics import ConfusionMatrix, EvaluationMetrics


def plot_confusion_matrix(
    cm: ConfusionMatrix,
    title: str = "Confusion Matrix",
    save_path: Optional[str] = None,
    show: bool = True
) -> None:
    """
    Plot confusion matrix using seaborn.
    
    Args:
        cm: ConfusionMatrix object
        title: Plot title
        save_path: Optional path to save the figure
        show: Whether to display the plot
    """
    # Create matrix
    matrix = np.array([
        [cm.true_positives, cm.false_positives],
        [cm.false_negatives, cm.true_negatives]
    ])
    
    # Create figure
    plt.figure(figsize=(8, 6))
    
    # Plot heatmap
    sns.heatmap(
        matrix,
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=['Predicted Positive', 'Predicted Negative'],
        yticklabels=['Actual Positive', 'Actual Negative'],
        cbar_kws={'label': 'Count'}
    )
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.ylabel('Actual', fontsize=12)
    plt.xlabel('Predicted', fontsize=12)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Confusion matrix saved to {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close()


def plot_metrics_comparison(
    metrics: EvaluationMetrics,
    save_path: Optional[str] = None,
    show: bool = True
) -> None:
    """
    Plot comparison of different metrics.
    
    Args:
        metrics: EvaluationMetrics object
        save_path: Optional path to save the figure
        show: Whether to display the plot
    """
    # Extract metrics
    metric_names = ['Precision', 'Recall', 'F1-Score', 'Accuracy']
    metric_values = [
        metrics.confusion_matrix.precision,
        metrics.confusion_matrix.recall,
        metrics.confusion_matrix.f1_score,
        metrics.confusion_matrix.accuracy,
    ]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create bar plot
    bars = ax.bar(metric_names, metric_values, color=['#3498db', '#2ecc71', '#e74c3c', '#f39c12'])
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            height,
            f'{height:.3f}',
            ha='center',
            va='bottom',
            fontweight='bold'
        )
    
    # Styling
    ax.set_ylim(0, 1.1)
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('Evaluation Metrics', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Metrics comparison saved to {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close()


def plot_category_breakdown(
    metrics: EvaluationMetrics,
    save_path: Optional[str] = None,
    show: bool = True
) -> None:
    """
    Plot metrics breakdown by category.
    
    Args:
        metrics: EvaluationMetrics object
        save_path: Optional path to save the figure
        show: Whether to display the plot
    """
    if not metrics.category_metrics:
        logger.warning("No category metrics to plot")
        return
    
    categories = list(metrics.category_metrics.keys())
    precision = [cm.precision for cm in metrics.category_metrics.values()]
    recall = [cm.recall for cm in metrics.category_metrics.values()]
    f1 = [cm.f1_score for cm in metrics.category_metrics.values()]
    
    x = np.arange(len(categories))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.bar(x - width, precision, width, label='Precision', color='#3498db')
    ax.bar(x, recall, width, label='Recall', color='#2ecc71')
    ax.bar(x + width, f1, width, label='F1-Score', color='#e74c3c')
    
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('Metrics by Category', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, 1.1)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Category breakdown saved to {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close()


def create_evaluation_report(
    metrics: EvaluationMetrics,
    output_dir: str = "evaluation_results"
) -> None:
    """
    Create comprehensive evaluation report with visualizations.
    
    Args:
        metrics: EvaluationMetrics object
        output_dir: Directory to save visualizations
    """
    from pathlib import Path
    from datetime import datetime
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate plots
    plot_confusion_matrix(
        metrics.confusion_matrix,
        save_path=str(output_path / f"confusion_matrix_{timestamp}.png"),
        show=False
    )
    
    plot_metrics_comparison(
        metrics,
        save_path=str(output_path / f"metrics_comparison_{timestamp}.png"),
        show=False
    )
    
    if metrics.category_metrics:
        plot_category_breakdown(
            metrics,
            save_path=str(output_path / f"category_breakdown_{timestamp}.png"),
            show=False
        )
    
    logger.info(f"Evaluation report created in {output_dir}")
