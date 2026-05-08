"""LangGraph orchestrator for multi-agent code review system."""

import uuid
from datetime import datetime
from typing import Dict, List

from langgraph.graph import END, StateGraph
from loguru import logger

from src.agents.bug_detector import BugDetectorAgent
from src.agents.models import AgentState, ReviewResult
from src.agents.quality_agent import QualityAgent
from src.agents.refactoring_agent import RefactoringAgent
from src.agents.security_agent import SecurityAgent
from src.core.config import Config
from src.core.utils import Timer, count_lines, hash_code


class CodeReviewOrchestrator:
    """Orchestrates multi-agent code review using LangGraph."""
    
    def __init__(self, config: Config):
        """Initialize orchestrator with all agents."""
        self.config = config
        
        # Initialize agents
        self.security_agent = SecurityAgent(config)
        self.bug_detector = BugDetectorAgent(config)
        self.refactoring_agent = RefactoringAgent(config)
        self.quality_agent = QualityAgent(config)
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("security", self._security_node)
        workflow.add_node("bug_detection", self._bug_detection_node)
        workflow.add_node("refactoring", self._refactoring_node)
        workflow.add_node("quality", self._quality_node)
        
        # Define the workflow
        # Start with security analysis
        workflow.set_entry_point("security")
        
        # Security -> Bug Detection
        workflow.add_edge("security", "bug_detection")
        
        # Bug Detection -> Refactoring (if enabled)
        workflow.add_conditional_edges(
            "bug_detection",
            self._should_refactor,
            {
                "refactor": "refactoring",
                "skip": "quality"
            }
        )
        
        # Refactoring -> Quality
        workflow.add_edge("refactoring", "quality")
        
        # Quality -> End
        workflow.add_edge("quality", END)
        
        return workflow.compile()
    
    def _security_node(self, state: AgentState) -> AgentState:
        """Security analysis node."""
        if self.config.enable_security_analysis:
            return self.security_agent.analyze(state)
        logger.info("Security analysis disabled")
        return state
    
    def _bug_detection_node(self, state: AgentState) -> AgentState:
        """Bug detection node."""
        if self.config.enable_bug_detection:
            return self.bug_detector.analyze(state)
        logger.info("Bug detection disabled")
        return state
    
    def _refactoring_node(self, state: AgentState) -> AgentState:
        """Refactoring analysis node."""
        if self.config.enable_refactoring:
            return self.refactoring_agent.analyze(state)
        logger.info("Refactoring disabled")
        return state
    
    def _quality_node(self, state: AgentState) -> AgentState:
        """Quality scoring node."""
        if self.config.enable_quality_scoring:
            return self.quality_agent.analyze(state)
        logger.info("Quality scoring disabled")
        return state
    
    def _should_refactor(self, state: AgentState) -> str:
        """Decide whether to run refactoring agent."""
        if self.config.enable_refactoring:
            return "refactor"
        return "skip"
    
    def review_code(
        self,
        code: str,
        language: str,
        file_path: str = None,
        options: Dict = None
    ) -> ReviewResult:
        """
        Execute complete code review workflow.
        
        Args:
            code: Source code to review
            language: Programming language
            file_path: Optional file path
            options: Optional review options
        
        Returns:
            ReviewResult with all analysis results
        """
        review_id = str(uuid.uuid4())
        
        logger.info(f"Starting code review {review_id} for {language} code")
        
        with Timer(f"Code review {review_id}") as timer:
            # Create initial state
            state = AgentState(
                code=code,
                language=language,
                file_path=file_path,
                options=options or {},
                review_id=review_id,
            )
            
            # Execute the graph
            try:
                final_state = self.graph.invoke(state)
                
                # Combine all issues
                all_issues = (
                    final_state.security_issues +
                    final_state.bug_issues
                )
                
                # Create result
                result = ReviewResult(
                    review_id=review_id,
                    timestamp=datetime.utcnow(),
                    language=language,
                    code_hash=hash_code(code),
                    issues=all_issues,
                    refactorings=final_state.refactorings,
                    quality_metrics=final_state.quality_metrics or self._default_metrics(),
                    total_lines=count_lines(code),
                    execution_time_seconds=timer.duration,
                    status="completed",
                    errors=final_state.errors,
                )
                
                logger.info(
                    f"Review {review_id} completed: "
                    f"{len(result.issues)} issues, "
                    f"{len(result.refactorings)} refactorings, "
                    f"score: {result.quality_metrics.overall_score}/100"
                )
                
                return result
            
            except Exception as e:
                logger.error(f"Error during review {review_id}: {e}")
                
                # Return partial results
                return ReviewResult(
                    review_id=review_id,
                    timestamp=datetime.utcnow(),
                    language=language,
                    code_hash=hash_code(code),
                    issues=[],
                    refactorings=[],
                    quality_metrics=self._default_metrics(),
                    total_lines=count_lines(code),
                    execution_time_seconds=timer.duration,
                    status="failed",
                    errors=[str(e)],
                )
    
    def _default_metrics(self):
        """Get default quality metrics."""
        from src.agents.models import QualityMetrics
        
        return QualityMetrics(
            overall_score=0,
            maintainability=0,
            reliability=0,
            security=0,
            performance=0,
            complexity=0,
        )
    
    def review_file(self, file_path: str) -> ReviewResult:
        """
        Review a code file.
        
        Args:
            file_path: Path to code file
        
        Returns:
            ReviewResult
        """
        from src.core.utils import detect_language, read_file
        
        code = read_file(file_path)
        language = detect_language(file_path)
        
        if not language:
            raise ValueError(f"Could not detect language for {file_path}")
        
        return self.review_code(code, language, file_path)
    
    async def review_code_async(
        self,
        code: str,
        language: str,
        file_path: str = None,
        options: Dict = None
    ) -> ReviewResult:
        """Async version of review_code."""
        # For now, just wrap synchronous version
        # In production, would implement async graph execution
        return self.review_code(code, language, file_path, options)
