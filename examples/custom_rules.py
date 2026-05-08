"""Example: Adding custom validation rules."""

from src.agents.models import IssueCategory, Severity
from src.agents.orchestrator import CodeReviewOrchestrator
from src.analysis.rule_validator import RuleValidator
from src.core.config import Config

def main():
    # Initialize
    config = Config.from_env()
    config.setup_logging()
    
    # Create rule validator
    validator = RuleValidator()
    
    # Add custom rules
    print("Adding custom rules...\n")
    
    # Rule 1: Detect TODO comments with specific format
    validator.add_custom_rule(
        language="python",
        name="todo_with_jira",
        pattern=r"#\s*TODO:\s*(?!JIRA-\d+)",
        category=IssueCategory.MAINTAINABILITY,
        severity=Severity.LOW,
        title="TODO without JIRA ticket",
        description="TODO comments should reference a JIRA ticket",
        recommendation="Add JIRA ticket reference: # TODO: JIRA-1234 ..."
    )
    
    # Rule 2: Detect deprecated function usage
    validator.add_custom_rule(
        language="python",
        name="deprecated_function",
        pattern=r"old_deprecated_function\s*\(",
        category=IssueCategory.MAINTAINABILITY,
        severity=Severity.MEDIUM,
        title="Use of deprecated function",
        description="old_deprecated_function() is deprecated",
        recommendation="Use new_recommended_function() instead"
    )
    
    # Rule 3: Detect missing docstrings in public functions
    validator.add_custom_rule(
        language="python",
        name="missing_docstring",
        pattern=r'def\s+(?!_)[a-zA-Z_]\w*\s*\([^)]*\):\s*\n\s+(?!""")',
        category=IssueCategory.MAINTAINABILITY,
        severity=Severity.LOW,
        title="Missing docstring",
        description="Public functions should have docstrings",
        recommendation="Add docstring to document function purpose and parameters"
    )
    
    # Rule 4: Company-specific security rule
    validator.add_custom_rule(
        language="python",
        name="internal_api_key",
        pattern=r'INTERNAL_API_KEY\s*=\s*["\'][^"\']+["\']',
        category=IssueCategory.SECURITY,
        severity=Severity.CRITICAL,
        title="Hardcoded internal API key",
        description="Internal API keys must not be hardcoded",
        recommendation="Use environment variables or company secret manager"
    )
    
    # Test code with custom rule violations
    test_code = """
# TODO: Fix this later
def calculate_price(quantity, price):
    total = quantity * price
    return total

# TODO: JIRA-1234 Optimize this
def optimized_function():
    '''This function has a proper JIRA reference.'''
    pass

def process_data(data):
    # Missing docstring - will be flagged
    result = old_deprecated_function(data)
    return result

# Security violation
INTERNAL_API_KEY = "sk-1234567890abcdef"

def get_config():
    config = {
        'api_key': INTERNAL_API_KEY
    }
    return config
"""
    
    print("Validating code with custom rules...\n")
    
    # Run validation
    issues = validator.validate(test_code, "python")
    
    print(f"Found {len(issues)} custom rule violations:\n")
    
    for issue in issues:
        print(f"[{issue.severity.value.upper()}] {issue.title}")
        print(f"  Category: {issue.category.value}")
        print(f"  Line: {issue.line_start}")
        print(f"  Description: {issue.description}")
        print(f"  Recommendation: {issue.recommendation}")
        print(f"  Rule: {issue.metadata.get('rule')}")
        print()
    
    # You can also integrate custom validator with the orchestrator
    print("\n" + "="*60)
    print("INTEGRATION WITH ORCHESTRATOR")
    print("="*60)
    
    orchestrator = CodeReviewOrchestrator(config)
    
    # Review the same code
    result = orchestrator.review_code(test_code, "python")
    
    print(f"\nTotal issues (including custom rules): {len(result.issues)}")
    print(f"Quality Score: {result.quality_metrics.overall_score}/100")
    
    # Filter custom rule issues
    custom_issues = [i for i in result.issues if "rule_validator" in i.source]
    print(f"Issues from custom rules: {len(custom_issues)}")


if __name__ == "__main__":
    main()
