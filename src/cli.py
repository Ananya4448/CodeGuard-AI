"""Command-line interface for CodeReview-Agent."""

import argparse
import json
import sys
from pathlib import Path

from loguru import logger

from src.agents.orchestrator import CodeReviewOrchestrator
from src.core.config import Config
from src.core.utils import detect_language, read_file


def setup_cli():
    """Setup CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="CodeReview-Agent: Multi-agent LLM code review system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single file
  python -m src.cli analyze --file app.py
  
  # Analyze a directory
  python -m src.cli analyze --dir src/
  
  # Generate JSON report
  python -m src.cli analyze --file app.py --report json --output report.json
  
  # Run benchmark evaluation
  python -m src.cli benchmark
  
  # Start API server
  python -m src.cli serve
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze code for issues")
    analyze_parser.add_argument("--file", "-f", type=str, help="File to analyze")
    analyze_parser.add_argument("--dir", "-d", type=str, help="Directory to analyze")
    analyze_parser.add_argument("--language", "-l", type=str, help="Programming language")
    analyze_parser.add_argument(
        "--report",
        "-r",
        type=str,
        choices=["console", "json", "html"],
        default="console",
        help="Report format"
    )
    analyze_parser.add_argument("--output", "-o", type=str, help="Output file path")
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Run benchmark evaluation")
    benchmark_parser.add_argument(
        "--dataset",
        type=str,
        help="Path to benchmark dataset"
    )
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument("--host", type=str, help="Server host")
    serve_parser.add_argument("--port", type=int, help="Server port")
    
    return parser


def analyze_command(args):
    """Handle analyze command."""
    config = Config.from_env()
    config.setup_logging()
    
    orchestrator = CodeReviewOrchestrator(config)
    
    if args.file:
        # Analyze single file
        logger.info(f"Analyzing file: {args.file}")
        
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"File not found: {args.file}")
            sys.exit(1)
        
        code = read_file(args.file)
        language = args.language or detect_language(args.file)
        
        if not language:
            logger.error(f"Could not detect language for {args.file}")
            sys.exit(1)
        
        result = orchestrator.review_code(code, language, args.file)
        
        # Output result
        if args.report == "console":
            print_console_report(result)
        elif args.report == "json":
            output_json_report(result, args.output)
        elif args.report == "html":
            output_html_report(result, args.output)
    
    elif args.dir:
        # Analyze directory
        logger.info(f"Analyzing directory: {args.dir}")
        
        dir_path = Path(args.dir)
        if not dir_path.exists():
            logger.error(f"Directory not found: {args.dir}")
            sys.exit(1)
        
        results = analyze_directory(orchestrator, dir_path, config.supported_languages_list)
        
        # Output aggregated results
        print(f"\nAnalyzed {len(results)} files")
        for file_path, result in results.items():
            print(f"\n{file_path}:")
            print(f"  Quality Score: {result.quality_metrics.overall_score}/100")
            print(f"  Issues: {len(result.issues)}")
    
    else:
        logger.error("Please specify --file or --dir")
        sys.exit(1)


def analyze_directory(orchestrator, dir_path: Path, languages: list) -> dict:
    """Analyze all code files in directory."""
    results = {}
    
    # Map extensions to languages
    ext_map = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "java": "java",
        "go": "go",
    }
    
    for lang in languages:
        for ext, lang_name in ext_map.items():
            if lang_name == lang:
                for file_path in dir_path.rglob(f"*.{ext}"):
                    try:
                        code = read_file(str(file_path))
                        result = orchestrator.review_code(code, lang, str(file_path))
                        results[str(file_path)] = result
                    except Exception as e:
                        logger.error(f"Error analyzing {file_path}: {e}")
    
    return results


def print_console_report(result):
    """Print report to console."""
    print("\n" + "="*70)
    print("CODE REVIEW REPORT")
    print("="*70)
    
    print(f"\nLanguage: {result.language}")
    print(f"Review ID: {result.review_id}")
    print(f"Timestamp: {result.timestamp}")
    print(f"Execution Time: {result.execution_time_seconds:.2f}s")
    
    print(f"\n{'QUALITY METRICS':-^70}")
    print(f"Overall Score:     {result.quality_metrics.overall_score}/100")
    print(f"Maintainability:   {result.quality_metrics.maintainability}/100")
    print(f"Reliability:       {result.quality_metrics.reliability}/100")
    print(f"Security:          {result.quality_metrics.security}/100")
    print(f"Performance:       {result.quality_metrics.performance}/100")
    print(f"Complexity:        {result.quality_metrics.complexity}/100")
    
    print(f"\n{'ISSUES FOUND':-^70}")
    print(f"Total Issues: {len(result.issues)}")
    
    if result.issues:
        # Group by severity
        from src.agents.models import Severity
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            issues = [i for i in result.issues if i.severity == severity]
            if issues:
                print(f"\n{severity.value.upper()} ({len(issues)}):")
                for issue in issues:
                    print(f"  [{issue.category.value}] {issue.title}")
                    if issue.line_start:
                        print(f"    Line {issue.line_start}: {issue.description}")
                    else:
                        print(f"    {issue.description}")
                    if issue.recommendation:
                        print(f"    → {issue.recommendation}")
    
    if result.refactorings:
        print(f"\n{'REFACTORING SUGGESTIONS':-^70}")
        print(f"Total Suggestions: {len(result.refactorings)}")
        
        for i, refactoring in enumerate(result.refactorings[:5], 1):  # Show top 5
            print(f"\n{i}. {refactoring.title}")
            print(f"   {refactoring.description}")
            if refactoring.benefits:
                print(f"   Benefits: {', '.join(refactoring.benefits)}")
    
    print("\n" + "="*70)


def output_json_report(result, output_file):
    """Output report as JSON."""
    output_file = output_file or f"review_{result.review_id}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result.to_json())
    
    logger.info(f"JSON report saved to {output_file}")
    print(f"Report saved to: {output_file}")


def output_html_report(result, output_file):
    """Output report as HTML."""
    output_file = output_file or f"review_{result.review_id}.html"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Code Review Report - {result.review_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #ecf0f1; border-radius: 5px; }}
        .issue {{ margin: 10px 0; padding: 10px; border-left: 4px solid #e74c3c; background: #fadbd8; }}
        .critical {{ border-left-color: #c0392b; background: #f5b7b1; }}
        .high {{ border-left-color: #e74c3c; background: #fadbd8; }}
        .medium {{ border-left-color: #f39c12; background: #fdeaa8; }}
        .low {{ border-left-color: #3498db; background: #d6eaf8; }}
        .score {{ font-size: 48px; font-weight: bold; color: #27ae60; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Code Review Report</h1>
        <p><strong>Review ID:</strong> {result.review_id}</p>
        <p><strong>Language:</strong> {result.language}</p>
        <p><strong>Timestamp:</strong> {result.timestamp}</p>
        
        <h2>Quality Score</h2>
        <div class="score">{result.quality_metrics.overall_score}/100</div>
        
        <h2>Metrics</h2>
        <div class="metric">Maintainability: {result.quality_metrics.maintainability}/100</div>
        <div class="metric">Reliability: {result.quality_metrics.reliability}/100</div>
        <div class="metric">Security: {result.quality_metrics.security}/100</div>
        <div class="metric">Performance: {result.quality_metrics.performance}/100</div>
        
        <h2>Issues Found ({len(result.issues)})</h2>
"""
    
    for issue in result.issues:
        html += f"""
        <div class="issue {issue.severity.value}">
            <strong>[{issue.severity.value.upper()}] {issue.title}</strong><br>
            <em>{issue.category.value}</em><br>
            {issue.description}<br>
            {f'<small>Line {issue.line_start}</small>' if issue.line_start else ''}
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    logger.info(f"HTML report saved to {output_file}")
    print(f"Report saved to: {output_file}")


def benchmark_command(args):
    """Handle benchmark command."""
    from src.evaluation.benchmark import Benchmark
    
    config = Config.from_env()
    config.setup_logging()
    
    benchmark = Benchmark(config, args.dataset)
    metrics = benchmark.run()
    
    print(f"\nBenchmark completed!")
    print(f"F1 Score: {metrics.confusion_matrix.f1_score:.3f}")


def serve_command(args):
    """Handle serve command."""
    from src.api.server import run_server
    
    config = Config.from_env()
    
    if args.host:
        config.api_host = args.host
    if args.port:
        config.api_port = args.port
    
    run_server()


def main():
    """Main CLI entry point."""
    parser = setup_cli()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    if args.command == "analyze":
        analyze_command(args)
    elif args.command == "benchmark":
        benchmark_command(args)
    elif args.command == "serve":
        serve_command(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
