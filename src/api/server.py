"""FastAPI backend server for code review service."""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.agents.orchestrator import CodeReviewOrchestrator
from src.core.config import Config, get_config


# Global orchestrator instance
orchestrator: CodeReviewOrchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    global orchestrator
    config = get_config()
    config.setup_logging()
    
    logger.info("Initializing Code Review Orchestrator...")
    orchestrator = CodeReviewOrchestrator(config)
    logger.info("Code Review Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Code Review Service")


def create_app(config: Config = None) -> FastAPI:
    """Create and configure FastAPI application."""
    if config is None:
        config = get_config()
    
    app = FastAPI(
        title="CodeReview-Agent API",
        description="Multi-agent LLM code review system with bug detection and refactoring",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    from src.api.routes import router
    app.include_router(router, prefix="/api/v1")
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "service": "CodeReview-Agent",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "orchestrator": "initialized" if orchestrator else "not initialized"
        }
    
    return app


def run_server():
    """Run the FastAPI server."""
    config = get_config()
    config.setup_logging()
    
    logger.info(f"Starting server on {config.api_host}:{config.api_port}")
    
    app = create_app(config)
    
    uvicorn.run(
        app,
        host=config.api_host,
        port=config.api_port,
        reload=config.api_reload,
        log_level=config.log_level.lower(),
    )


if __name__ == "__main__":
    run_server()
