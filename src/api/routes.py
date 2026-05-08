"""API routes for code review service."""

import asyncio
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, BackgroundTasks
from loguru import logger
from pydantic import BaseModel, Field

from src.agents.models import ReviewRequest, ReviewResponse, ReviewResult
from src.core.config import get_config


router = APIRouter()

# In-memory storage for review results (in production, use Redis or database)
review_store: Dict[str, ReviewResult] = {}
review_status: Dict[str, str] = {}


class CodeReviewRequest(BaseModel):
    """Request model for code review."""
    code: str = Field(..., description="Source code to review", min_length=1)
    language: str = Field(..., description="Programming language (python, javascript, etc.)")
    file_path: Optional[str] = Field(None, description="Optional file path")
    options: Dict[str, bool] = Field(
        default_factory=lambda: {
            "check_security": True,
            "check_bugs": True,
            "suggest_refactoring": True,
            "calculate_metrics": True,
        },
        description="Review options"
    )


class ReviewStatusResponse(BaseModel):
    """Response model for review status."""
    review_id: str
    status: str  # pending, processing, completed, failed
    message: Optional[str] = None


@router.post("/review", response_model=ReviewResponse)
async def create_review(request: CodeReviewRequest, background_tasks: BackgroundTasks):
    """
    Submit code for review.
    
    Returns review ID immediately and processes in background.
    """
    review_id = str(uuid4())
    
    logger.info(f"Received review request {review_id} for {request.language} code")
    
    # Mark as processing
    review_status[review_id] = "processing"
    
    # Add to background tasks
    background_tasks.add_task(
        process_review,
        review_id,
        request.code,
        request.language,
        request.file_path,
        request.options
    )
    
    return ReviewResponse(
        review_id=review_id,
        status="processing",
        message="Review submitted successfully. Use /review/{review_id} to check status."
    )


@router.post("/review/sync", response_model=ReviewResponse)
async def create_review_sync(request: CodeReviewRequest):
    """
    Submit code for review and wait for completion (synchronous).
    
    Returns complete review result.
    """
    review_id = str(uuid4())
    
    logger.info(f"Received synchronous review request {review_id} for {request.language} code")
    
    try:
        # Import orchestrator
        from src.api.server import orchestrator
        
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not initialized")
        
        # Process review
        result = orchestrator.review_code(
            code=request.code,
            language=request.language,
            file_path=request.file_path,
            options=request.options
        )
        
        # Store result
        review_store[review_id] = result
        review_status[review_id] = "completed"
        
        return ReviewResponse(
            review_id=review_id,
            status="completed",
            result=result,
            message="Review completed successfully"
        )
    
    except Exception as e:
        logger.error(f"Error processing review {review_id}: {e}")
        review_status[review_id] = "failed"
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")


@router.get("/review/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: str):
    """
    Get review status and result by ID.
    """
    if review_id not in review_status:
        raise HTTPException(status_code=404, detail="Review not found")
    
    status = review_status[review_id]
    result = review_store.get(review_id)
    
    return ReviewResponse(
        review_id=review_id,
        status=status,
        result=result,
        message=f"Review status: {status}"
    )


@router.get("/review/{review_id}/status", response_model=ReviewStatusResponse)
async def get_review_status(review_id: str):
    """
    Get review status only (without full result).
    """
    if review_id not in review_status:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return ReviewStatusResponse(
        review_id=review_id,
        status=review_status[review_id],
        message=f"Current status: {review_status[review_id]}"
    )


@router.get("/reviews")
async def list_reviews(limit: int = 10, offset: int = 0):
    """
    List recent reviews.
    """
    review_ids = list(review_store.keys())
    total = len(review_ids)
    
    # Paginate
    paginated_ids = review_ids[offset:offset + limit]
    
    reviews = []
    for review_id in paginated_ids:
        result = review_store[review_id]
        reviews.append({
            "review_id": review_id,
            "language": result.language,
            "timestamp": result.timestamp.isoformat(),
            "status": review_status.get(review_id, "unknown"),
            "issues_count": len(result.issues),
            "quality_score": result.quality_metrics.overall_score,
        })
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "reviews": reviews
    }


@router.get("/metrics")
async def get_metrics():
    """
    Get aggregate metrics across all reviews.
    """
    if not review_store:
        return {
            "total_reviews": 0,
            "message": "No reviews yet"
        }
    
    total_reviews = len(review_store)
    total_issues = sum(len(r.issues) for r in review_store.values())
    avg_quality_score = sum(r.quality_metrics.overall_score for r in review_store.values()) / total_reviews
    
    # Count by severity
    from src.agents.models import Severity
    severity_counts = {s.value: 0 for s in Severity}
    
    for result in review_store.values():
        for issue in result.issues:
            severity_counts[issue.severity.value] += 1
    
    # Count by category
    from src.agents.models import IssueCategory
    category_counts = {c.value: 0 for c in IssueCategory}
    
    for result in review_store.values():
        for issue in result.issues:
            category_counts[issue.category.value] += 1
    
    return {
        "total_reviews": total_reviews,
        "total_issues": total_issues,
        "average_quality_score": round(avg_quality_score, 2),
        "issues_by_severity": severity_counts,
        "issues_by_category": category_counts,
    }


@router.delete("/review/{review_id}")
async def delete_review(review_id: str):
    """
    Delete a review by ID.
    """
    if review_id not in review_status:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review_store.pop(review_id, None)
    review_status.pop(review_id, None)
    
    return {"message": f"Review {review_id} deleted successfully"}


# Background task function
async def process_review(
    review_id: str,
    code: str,
    language: str,
    file_path: Optional[str],
    options: Dict
):
    """Process review in background."""
    try:
        from src.api.server import orchestrator
        
        if not orchestrator:
            logger.error("Orchestrator not initialized")
            review_status[review_id] = "failed"
            return
        
        # Process review
        result = orchestrator.review_code(
            code=code,
            language=language,
            file_path=file_path,
            options=options
        )
        
        # Store result
        review_store[review_id] = result
        review_status[review_id] = "completed"
        
        logger.info(f"Review {review_id} completed successfully")
    
    except Exception as e:
        logger.error(f"Error processing review {review_id}: {e}")
        review_status[review_id] = "failed"
