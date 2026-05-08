"""Example: Batch processing multiple files."""

import json
from pathlib import Path
from typing import Dict, List

from loguru import logger

from src.agents.orchestrator import CodeReviewOrchestrator
from src.core.config import Config
from src.core.utils import detect_language, read_file


def batch_review_directory(directory: str, output_file: str = "batch_results.json"):
    """
    Review all code files in a directory.
    
    Args:
        directory: Directory path to scan
        output_file: Output file for results
    """
    config = Config.from_env()
    config.setup_logging()
    
    orchestrator = CodeReviewOrchestrator(config)
    
    # Supported extensions
    extensions = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".go": "go",
    }
    
    results = {}
    dir_path = Path(directory)
    
    # Find all code files
    code_files = []
    for ext, lang in extensions.items():
        code_files.extend(dir_path.rglob(f"*{ext}"))
    
    print(f"\nFound {len(code_files)} code files to review")
    print("="*60)
    
    # Review each file
    for i, file_path in enumerate(code_files, 1):
        try:
            print(f"\n[{i}/{len(code_files)}] Reviewing: {file_path.name}")
            
            # Read code
            code = read_file(str(file_path))
            language = detect_language(str(file_path))
            
            if not language:
                logger.warning(f"Could not detect language for {file_path}")
                continue
            
            # Review
            result = orchestrator.review_code(code, language, str(file_path))
            
            # Store results
            results[str(file_path)] = {
                "quality_score": result.quality_metrics.overall_score,
                "issues_count": len(result.issues),
                "critical_issues": len(result.get_critical_issues()),
                "security_issues": len(result.get_security_issues()),
                "refactorings_count": len(result.refactorings),
                "execution_time": result.execution_time_seconds,
                "issues": [
                    {
                        "severity": issue.severity.value,
                        "category": issue.category.value,
                        "title": issue.title,
                        "line": issue.line_start,
                    }
                    for issue in result.issues
                ]
            }
            
            print(f"  Quality Score: {result.quality_metrics.overall_score}/100")
            print(f"  Issues: {len(result.issues)}")
            print(f"  Critical: {len(result.get_critical_issues())}")
            
        except Exception as e:
            logger.error(f"Error reviewing {file_path}: {e}")
            results[str(file_path)] = {"error": str(e)}
    
    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*60)
    print(f"Results saved to: {output_file}")
    
    # Summary
    print_batch_summary(results)


def print_batch_summary(results: Dict):
    """Print summary of batch review."""
    print("\n" + "="*60)
    print("BATCH REVIEW SUMMARY")
    print("="*60)
    
    total_files = len(results)
    successful = sum(1 for r in results.values() if "error" not in r)
    failed = total_files - successful
    
    print(f"\nFiles Reviewed: {successful}/{total_files}")
    if failed > 0:
        print(f"Failed: {failed}")
    
    if successful > 0:
        # Calculate averages
        avg_score = sum(
            r["quality_score"] for r in results.values() if "error" not in r
        ) / successful
        
        total_issues = sum(
            r["issues_count"] for r in results.values() if "error" not in r
        )
        
        total_critical = sum(
            r["critical_issues"] for r in results.values() if "error" not in r
        )
        
        total_security = sum(
            r["security_issues"] for r in results.values() if "error" not in r
        )
        
        print(f"\nAverage Quality Score: {avg_score:.1f}/100")
        print(f"Total Issues Found: {total_issues}")
        print(f"Critical Issues: {total_critical}")
        print(f"Security Issues: {total_security}")
        
        # Top problematic files
        print("\nFiles with Most Issues:")
        sorted_files = sorted(
            [(path, data) for path, data in results.items() if "error" not in data],
            key=lambda x: x[1]["issues_count"],
            reverse=True
        )[:5]
        
        for path, data in sorted_files:
            print(f"  {Path(path).name}: {data['issues_count']} issues (Score: {data['quality_score']}/100)")
        
        # Best quality files
        print("\nHighest Quality Files:")
        best_files = sorted(
            [(path, data) for path, data in results.items() if "error" not in data],
            key=lambda x: x[1]["quality_score"],
            reverse=True
        )[:5]
        
        for path, data in best_files:
            print(f"  {Path(path).name}: {data['quality_score']}/100")


def compare_reviews(results_file1: str, results_file2: str):
    """
    Compare two batch review results (e.g., before/after refactoring).
    
    Args:
        results_file1: First results file
        results_file2: Second results file
    """
    with open(results_file1, 'r') as f:
        results1 = json.load(f)
    
    with open(results_file2, 'r') as f:
        results2 = json.load(f)
    
    print("\n" + "="*60)
    print("COMPARISON REPORT")
    print("="*60)
    
    # Find common files
    common_files = set(results1.keys()) & set(results2.keys())
    
    improvements = []
    regressions = []
    
    for file_path in common_files:
        r1 = results1[file_path]
        r2 = results2[file_path]
        
        if "error" in r1 or "error" in r2:
            continue
        
        score_diff = r2["quality_score"] - r1["quality_score"]
        issues_diff = r2["issues_count"] - r1["issues_count"]
        
        if score_diff > 0 or issues_diff < 0:
            improvements.append((file_path, score_diff, issues_diff))
        elif score_diff < 0 or issues_diff > 0:
            regressions.append((file_path, score_diff, issues_diff))
    
    print(f"\nFiles Compared: {len(common_files)}")
    print(f"Improvements: {len(improvements)}")
    print(f"Regressions: {len(regressions)}")
    print(f"Unchanged: {len(common_files) - len(improvements) - len(regressions)}")
    
    if improvements:
        print("\nTop Improvements:")
        for file_path, score_diff, issues_diff in sorted(improvements, key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {Path(file_path).name}:")
            print(f"    Score: +{score_diff:.1f} points")
            print(f"    Issues: {issues_diff:+d}")
    
    if regressions:
        print("\nRegressions:")
        for file_path, score_diff, issues_diff in sorted(regressions, key=lambda x: x[1])[:5]:
            print(f"  {Path(file_path).name}:")
            print(f"    Score: {score_diff:.1f} points")
            print(f"    Issues: {issues_diff:+d}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python batch_processing.py <directory>")
        print("  python batch_processing.py compare <file1.json> <file2.json>")
        sys.exit(1)
    
    if sys.argv[1] == "compare":
        if len(sys.argv) < 4:
            print("Error: compare requires two result files")
            sys.exit(1)
        compare_reviews(sys.argv[2], sys.argv[3])
    else:
        directory = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "batch_results.json"
        batch_review_directory(directory, output_file)
