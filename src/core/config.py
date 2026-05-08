"""Core configuration management for CodeReview-Agent."""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Main configuration class for the application."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, validation_alias="ANTHROPIC_API_KEY")
    model_provider: str = Field("openai", validation_alias="MODEL_PROVIDER")
    model_name: str = Field("gpt-4-turbo-preview", validation_alias="MODEL_NAME")
    
    # LangSmith
    langchain_tracing_v2: bool = Field(False, validation_alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: Optional[str] = Field(None, validation_alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field("codereview-agent", validation_alias="LANGCHAIN_PROJECT")
    
    # API Configuration
    api_host: str = Field("0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(8000, validation_alias="API_PORT")
    api_workers: int = Field(4, validation_alias="API_WORKERS")
    api_reload: bool = Field(False, validation_alias="API_RELOAD")
    
    # Analysis Configuration
    max_file_size_mb: int = Field(5, validation_alias="MAX_FILE_SIZE_MB")
    supported_languages: str = Field(
        "python,javascript,typescript,java,go",
        validation_alias="SUPPORTED_LANGUAGES"
    )
    enable_security_analysis: bool = Field(True, validation_alias="ENABLE_SECURITY_ANALYSIS")
    enable_bug_detection: bool = Field(True, validation_alias="ENABLE_BUG_DETECTION")
    enable_refactoring: bool = Field(True, validation_alias="ENABLE_REFACTORING")
    enable_quality_scoring: bool = Field(True, validation_alias="ENABLE_QUALITY_SCORING")
    
    # Static Analysis
    pylint_enabled: bool = Field(True, validation_alias="PYLINT_ENABLED")
    flake8_enabled: bool = Field(True, validation_alias="FLAKE8_ENABLED")
    bandit_enabled: bool = Field(True, validation_alias="BANDIT_ENABLED")
    mypy_enabled: bool = Field(True, validation_alias="MYPY_ENABLED")
    
    # Evaluation
    evaluation_dataset_path: str = Field(
        "./data/evaluation_dataset.json",
        validation_alias="EVALUATION_DATASET_PATH"
    )
    confidence_threshold: float = Field(0.7, validation_alias="CONFIDENCE_THRESHOLD")
    min_quality_score: int = Field(60, validation_alias="MIN_QUALITY_SCORE")
    
    # Performance
    max_concurrent_reviews: int = Field(10, validation_alias="MAX_CONCURRENT_REVIEWS")
    agent_timeout_seconds: int = Field(300, validation_alias="AGENT_TIMEOUT_SECONDS")
    cache_enabled: bool = Field(True, validation_alias="CACHE_ENABLED")
    cache_ttl_seconds: int = Field(3600, validation_alias="CACHE_TTL_SECONDS")
    
    # Database
    database_url: str = Field(
        "sqlite:///./codereview.db",
        validation_alias="DATABASE_URL"
    )
    
    # Logging
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")
    log_format: str = Field("json", validation_alias="LOG_FORMAT")
    log_file: str = Field("logs/codereview.log", validation_alias="LOG_FILE")
    
    # Security
    secret_key: str = Field(
        "change_this_secret_key_in_production",
        validation_alias="SECRET_KEY"
    )
    allowed_origins: str = Field(
        "http://localhost:3000,http://localhost:8000",
        validation_alias="ALLOWED_ORIGINS"
    )
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(True, validation_alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(100, validation_alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(60, validation_alias="RATE_LIMIT_WINDOW_SECONDS")
    
    @property
    def supported_languages_list(self) -> List[str]:
        """Get supported languages as a list."""
        return [lang.strip() for lang in self.supported_languages.split(",")]
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Get allowed origins as a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls()
    
    def get_llm_config(self) -> dict:
        """Get LLM configuration dictionary."""
        if self.model_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.model_name,
                "temperature": 0.1,
            }
        elif self.model_provider == "anthropic":
            return {
                "provider": "anthropic",
                "api_key": self.anthropic_api_key,
                "model": self.model_name,
                "temperature": 0.1,
            }
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")
    
    def setup_logging(self) -> None:
        """Setup logging configuration."""
        from loguru import logger
        import sys
        
        # Remove default handler
        logger.remove()
        
        # Add custom handlers
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        # Console handler
        logger.add(
            sys.stderr,
            format=log_format,
            level=self.log_level,
            colorize=True,
        )
        
        # File handler
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            self.log_file,
            format=log_format,
            level=self.log_level,
            rotation="100 MB",
            retention="30 days",
            compression="zip",
        )


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def set_config(config: Config) -> None:
    """Set global configuration instance."""
    global _config
    _config = config
