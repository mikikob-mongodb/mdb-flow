#!/usr/bin/env python3
"""
Shared utilities for setup scripts.

Common functionality used across multiple setup scripts including:
- Database connection helpers
- Pretty colored output
- Verification helpers
- API testing

Usage:
    from utils import print_success, print_error, test_connection

    success, error = test_connection()
    if success:
        print_success("MongoDB connected")
    else:
        print_error(f"Connection failed: {error}")
"""

import os
import sys
from typing import Tuple, Optional, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv not installed, env vars must be set manually

# Try to import colorama for cross-platform colored output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)  # Auto-reset colors after each print
    COLORS_AVAILABLE = True
except ImportError:
    # Fallback if colorama not installed
    COLORS_AVAILABLE = False

    class Fore:
        GREEN = ""
        YELLOW = ""
        RED = ""
        BLUE = ""
        CYAN = ""
        RESET = ""

    class Style:
        BRIGHT = ""
        RESET_ALL = ""


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_database():
    """
    Get MongoDB database connection using shared/config.py settings.

    Returns:
        Database instance from MongoDB().get_database()

    Raises:
        Exception if connection fails
    """
    from shared.db import MongoDB

    mongodb = MongoDB()
    db = mongodb.get_database()
    return db


def test_connection() -> Tuple[bool, str]:
    """
    Test MongoDB connection.

    Returns:
        Tuple of (success: bool, error_message: str)
        If success is True, error_message will be empty string
        If success is False, error_message contains the error details
    """
    try:
        from shared.db import MongoDB
        from shared.config import settings

        mongodb = MongoDB()
        db = mongodb.get_database()

        # Try to list collections to verify connection works
        db.list_collection_names()

        return True, ""

    except Exception as e:
        return False, str(e)


# =============================================================================
# PRETTY OUTPUT
# =============================================================================

def print_header(text: str):
    """
    Print formatted header with long separators.

    Example:
        print_header("🚀 Flow Companion Setup")
        # Output:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 🚀 Flow Companion Setup
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    separator = "━" * 67
    print(f"{Fore.CYAN}{separator}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{separator}{Style.RESET_ALL}")


def print_separator(length: int = 43):
    """
    Print visual separator.

    Args:
        length: Length of separator (default: 43)
    """
    print(f"{Fore.CYAN}{'━' * length}{Style.RESET_ALL}")


def print_success(text: str):
    """
    Print green checkmark + text.

    Args:
        text: Message to print

    Example:
        print_success("Database connected")
        # Output: ✅ Database connected (in green)
    """
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")


def print_warning(text: str):
    """
    Print yellow warning symbol + text.

    Args:
        text: Warning message to print

    Example:
        print_warning("Tavily API key not set")
        # Output: ⚠️  Tavily API key not set (in yellow)
    """
    print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")


def print_error(text: str):
    """
    Print red X + text.

    Args:
        text: Error message to print

    Example:
        print_error("Connection failed")
        # Output: ❌ Connection failed (in red)
    """
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")


def print_info(text: str):
    """
    Print blue info symbol + text.

    Args:
        text: Info message to print

    Example:
        print_info("Checking environment...")
        # Output: ℹ️  Checking environment... (in blue)
    """
    print(f"{Fore.BLUE}ℹ️  {text}{Style.RESET_ALL}")


def print_step(step_num: int, total: int, text: str):
    """
    Print step indicator in 'Step 1/4: text' format.

    Args:
        step_num: Current step number
        total: Total number of steps
        text: Step description

    Example:
        print_step(1, 4, "Checking environment...")
        # Output: Step 1/4: Checking environment... (in cyan)
    """
    print(f"{Fore.CYAN}{Style.BRIGHT}Step {step_num}/{total}: {text}{Style.RESET_ALL}")


# =============================================================================
# VERIFICATION
# =============================================================================

def check_env_var(name: str, required: bool = True) -> Tuple[bool, str]:
    """
    Check if environment variable is set.

    Args:
        name: Environment variable name
        required: If True, empty string counts as not set

    Returns:
        Tuple of (exists: bool, value_preview: str)
        value_preview is masked for security (first 6 chars + ...)
    """
    value = os.getenv(name)

    if value is None or (required and value == ""):
        return False, ""

    # Create preview (first 6 chars + ...)
    if len(value) > 10:
        preview = value[:6] + "..."
    else:
        preview = value

    return True, preview


def check_collection_exists(db, name: str) -> bool:
    """
    Check if collection exists in database.

    Args:
        db: MongoDB database instance
        name: Collection name

    Returns:
        True if collection exists, False otherwise
    """
    try:
        existing_collections = db.list_collection_names()
        return name in existing_collections
    except Exception:
        return False


def check_index_exists(db, collection: str, index_name: str) -> bool:
    """
    Check if index exists on collection.

    Args:
        db: MongoDB database instance
        collection: Collection name
        index_name: Index name to check

    Returns:
        True if index exists, False otherwise
    """
    try:
        coll = db[collection]
        indexes = list(coll.list_indexes())
        index_names = [idx["name"] for idx in indexes]
        return index_name in index_names
    except Exception:
        return False


def get_collection_count(db, collection: str, filter: Optional[Dict[str, Any]] = None) -> int:
    """
    Get document count in collection, optionally with filter.

    Args:
        db: MongoDB database instance
        collection: Collection name
        filter: Optional MongoDB filter query

    Returns:
        Document count (0 if collection doesn't exist or error)
    """
    try:
        coll = db[collection]
        if filter is None:
            return coll.count_documents({})
        else:
            return coll.count_documents(filter)
    except Exception:
        return 0


# =============================================================================
# API TESTING
# =============================================================================

def test_voyage_api() -> Tuple[bool, str]:
    """
    Test Voyage AI embedding API.

    Returns:
        Tuple of (success: bool, details: str)
        If success, details contains dimension info
        If failure, details contains error message
    """
    try:
        from shared.embeddings import embed_document

        # Test embedding generation
        test_text = "test embedding"
        embedding = embed_document(test_text)

        # Check dimensions
        if len(embedding) == 1024:
            return True, f"working (1024-dim embeddings)"
        else:
            return False, f"unexpected dimensions ({len(embedding)}, expected 1024)"

    except Exception as e:
        return False, f"failed ({str(e)})"


def test_anthropic_api() -> Tuple[bool, str]:
    """
    Test Anthropic API.

    Returns:
        Tuple of (success: bool, details: str)
        If success, details contains model info
        If failure, details contains error message
    """
    try:
        from anthropic import Anthropic

        # Default model used in the app
        model = "claude-sonnet-4-5-20250929"

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Make a simple completion request
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'ok'"}]
        )

        if response.content:
            return True, f"working ({model})"
        else:
            return False, "unexpected response"

    except Exception as e:
        return False, f"failed ({str(e)})"


def test_tavily_mcp() -> Tuple[bool, str]:
    """
    Test Tavily MCP connection.

    Returns:
        Tuple of (success: bool, details: str)
        If API key not set, returns (True, "not configured (optional)")
        If API key set, returns status
    """
    tavily_key = os.getenv("TAVILY_API_KEY")

    if not tavily_key:
        return True, "not configured (optional)"

    # For now, just check if key is set
    # Full MCP verification would require running the MCP server
    return True, "API key set"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def check_all_env_vars() -> Dict[str, Tuple[bool, str]]:
    """
    Check all required environment variables.

    Returns:
        Dictionary mapping variable names to (exists, preview) tuples
    """
    required_vars = [
        "ANTHROPIC_API_KEY",
        "VOYAGE_API_KEY",
        "OPENAI_API_KEY",
        "MONGODB_URI",
        "MONGODB_DATABASE"
    ]

    results = {}
    for var in required_vars:
        results[var] = check_env_var(var, required=True)

    return results


def check_all_collections(db) -> Dict[str, bool]:
    """
    Check all required collections exist.

    Args:
        db: MongoDB database instance

    Returns:
        Dictionary mapping collection names to existence status
    """
    required_collections = [
        "tasks",
        "projects",
        "short_term_memory",
        "long_term_memory",
        "shared_memory",
        "tool_discoveries",
    ]

    results = {}
    for collection in required_collections:
        results[collection] = check_collection_exists(db, collection)

    return results


def test_all_apis() -> Dict[str, Tuple[bool, str]]:
    """
    Test all API connections.

    Returns:
        Dictionary mapping API names to (success, details) tuples
    """
    return {
        "voyage": test_voyage_api(),
        "anthropic": test_anthropic_api(),
        "tavily": test_tavily_mcp()
    }


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    """Test the utility functions."""

    print_header("🧪 Testing Setup Utilities")
    print()

    # Test pretty printing
    print("Testing output functions:")
    print_success("This is a success message")
    print_warning("This is a warning message")
    print_error("This is an error message")
    print_info("This is an info message")
    print()

    print_step(1, 4, "Testing step indicator")
    print()

    # Test environment variables
    print("Testing environment variable checks:")
    env_results = check_all_env_vars()
    for var, (exists, preview) in env_results.items():
        if exists:
            print_success(f"{var}: {preview}")
        else:
            print_error(f"{var}: not set")
    print()

    # Test database connection
    print("Testing database connection:")
    success, error = test_connection()
    if success:
        print_success("MongoDB connection successful")

        # Test collections
        print()
        print("Checking collections:")
        db = get_database()
        coll_results = check_all_collections(db)
        for collection, exists in coll_results.items():
            if exists:
                count = get_collection_count(db, collection)
                print_success(f"{collection}: exists ({count} documents)")
            else:
                print_warning(f"{collection}: missing")
    else:
        print_error(f"MongoDB connection failed: {error}")

    print()
    print_separator()
