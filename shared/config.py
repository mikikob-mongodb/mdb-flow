"""Configuration management for Flow Companion."""

import os
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

    # Tavily (for MCP Agent)
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
