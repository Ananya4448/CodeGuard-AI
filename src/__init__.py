"""CodeReview-Agent: Multi-agent LLM code review system."""

__version__ = "1.0.0"
__author__ = "CodeReview-Agent Team"
__description__ = "Multi-agent LLM system for automated code review, bug detection, and refactoring"

from src.agents import CodeReviewOrchestrator
from src.core import Config, get_config

__all__ = [
    "CodeReviewOrchestrator",
    "Config",
    "get_config",
    "__version__",
]
