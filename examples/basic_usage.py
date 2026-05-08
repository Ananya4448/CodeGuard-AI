"""Basic usage example of CodeReview-Agent."""

from src.agents.orchestrator import CodeReviewOrchestrator
from src.core.config import Config

def main():
    # Initialize configuration
    config = Config.from_env()
    config.setup_logging()
    
    # Create orchestrator
    orchestrator = CodeReviewOrchestrator(config)
    
    # Example code to review
    code = """
def calculate_total(items, discount=None):
    total = 0
    for item in items:
        total = total + item['price']
    
    if discount:
        total = total - discount
    
    return total

def unsafe_login(username, password):
    # Security issue: hardcoded credentials
    admin_password = "admin123"
    
    # Bug: using eval
    if eval(f"'{password}' == '{admin_password}'"):
        return True
    return False

def process_data(data):
    # No error handling
    result = data.split(',')
    return result[0]
"""
    
    # Review the code
    print("Starting code review...\n")
    result = orchestrator.review_code(code, language="python")
    
    # Display results
    print("="*60)
    print(f"REVIEW RESULTS")
    print("="*60)
    
    print(f"\nQuality Score: {result.quality_metrics.overall_score}/100")
    print(f"Total Issues Found: {len(result.issues)}")
    print(f"Refactoring Suggestions: {len(result.refactorings)}")
    
    print("\n--- ISSUES ---")
    for issue in result.issues:
        print(f"\n[{issue.severity.value.upper()}] {issue.title}")
        print(f"  Category: {issue.category.value}")
        print(f"  Line: {issue.line_start}")
        print(f"  Description: {issue.description}")
        print(f"  Recommendation: {issue.recommendation}")
    
    print("\n--- REFACTORING SUGGESTIONS ---")
    for refactoring in result.refactorings:
        print(f"\n{refactoring.title}")
        print(f"  Priority: {refactoring.priority.value}")
        print(f"  Description: {refactoring.description}")
        print(f"  Benefits: {', '.join(refactoring.benefits)}")
    
    print("\n--- QUALITY METRICS ---")
    metrics = result.quality_metrics
    print(f"  Maintainability: {metrics.maintainability}/100")
    print(f"  Reliability: {metrics.reliability}/100")
    print(f"  Security: {metrics.security}/100")
    print(f"  Performance: {metrics.performance}/100")
    print(f"  Complexity: {metrics.complexity}/100")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
