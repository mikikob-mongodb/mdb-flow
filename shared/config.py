"""Configuration management for Flow Companion."""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Anthropic API
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")

    # Voyage AI
    voyage_api_key: str = Field(..., alias="VOYAGE_API_KEY")

    # OpenAI (for Whisper)
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")

    # MongoDB
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_database: str = Field(..., alias="MONGODB_DATABASE")

    # MCP Configuration
    # Tavily MCP
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")

    # MongoDB MCP
    mongodb_mcp_enabled: bool = Field(default=False, alias="MONGODB_MCP_ENABLED")

    # Experimental mode toggle (can be overridden at runtime)
    mcp_mode_enabled: bool = Field(default=False, alias="MCP_MODE_ENABLED")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def mcp_available(self) -> bool:
        """Returns True if any MCP server can be connected"""
        return bool(self.tavily_api_key) or self.mongodb_mcp_enabled


# Global settings instance
settings = Settings()
