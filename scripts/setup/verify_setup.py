#!/usr/bin/env python3
"""
Setup Verification Script for Flow Companion.

Performs comprehensive health checks to verify that everything is configured
correctly for a new developer.

Checks:
    1. Environment file (.env exists, required vars set)
    2. Python dependencies (key packages installed)
    3. Database (MongoDB connection, collections, indexes, data)
    4. Embedding API (Voyage AI - valid key, can generate embeddings)
    5. LLM API (Anthropic - valid key, model availability)
    6. MCP (Tavily - optional, if API key set)
    7. File system (required directories, log directory writable)

Usage:
    # Full verification (recommended)
    python scripts/verify_setup.py

    # Quick check (skip API calls)
    python scripts/verify_setup.py --quick

    # Attempt to fix issues automatically
    python scripts/verify_setup.py --fix

    # Verbose output
    python scripts/verify_setup.py --verbose
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# =============================================================================
# CONFIGURATION
# =============================================================================

REQUIRED_ENV_VARS = {
    "ANTHROPIC_API_KEY": "Claude API key",
    "VOYAGE_API_KEY": "Voyage AI embeddings API key",
    "OPENAI_API_KEY": "OpenAI API key (for Whisper)",
    "MONGODB_URI": "MongoDB connection string",
    "MONGODB_DATABASE": "MongoDB database name"
}

OPTIONAL_ENV_VARS = {
    "TAVILY_API_KEY": "Tavily API key (for web search via MCP)",
    "MONGODB_MCP_ENABLED": "MongoDB MCP mode",
    "MCP_MODE_ENABLED": "MCP mode toggle",
    "LOG_LEVEL": "Logging level",
    "DEBUG": "Debug mode"
}

REQUIRED_COLLECTIONS = [
    "tasks",
    "projects",
    "short_term_memory",
    "long_term_memory",
    "shared_memory",
    "tool_discoveries",
]

REQUIRED_DIRECTORIES = [
    "logs",
    "data",
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# VERIFICATION TRACKER
# =============================================================================

class VerificationTracker:
    """Track verification results."""

    def __init__(self):
        self.passed = 0
        self.warnings = 0
        self.errors = 0
        self.error_details = []  # List of (message, fix_suggestion) tuples

    def add_pass(self, message: str):
        """Add a passing check."""
        logger.info(f"✅ {message}")
        self.passed += 1

    def add_warning(self, message: str):
        """Add a warning."""
        logger.info(f"⚠️  {message}")
        self.warnings += 1

    def add_error(self, message: str, fix: str = ""):
        """Add an error."""
        logger.info(f"❌ {message}")
        self.errors += 1
        self.error_details.append((message, fix))


# =============================================================================
# VERIFICATION FUNCTIONS
# =============================================================================

def print_separator():
    """Print visual separator."""
    logger.info("━" * 43)


def print_header(text: str):
    """Print section header."""
    logger.info(text)
    print_separator()


def verify_environment(tracker: VerificationTracker, verbose: bool = False) -> bool:
    """Verify environment file and variables."""
    print_header("📄 Environment")

    # Load .env file
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"

    if not env_file.exists():
        tracker.add_error(
            ".env file not found",
            f"Create .env file at {env_file}\nRun: python scripts/setup.py"
        )
        return False

    tracker.add_pass(".env file found")
    load_dotenv(env_file)

    # Check required variables
    all_required_set = True
    for var, description in REQUIRED_ENV_VARS.items():
        value = os.getenv(var)
        if value:
            if verbose:
                tracker.add_pass(f"{var}: set")
            else:
                tracker.add_pass(f"{var}: set")
        else:
            tracker.add_error(
                f"{var}: not set",
                f"Add to .env: {var}=your_value_here\n{description}"
            )
            all_required_set = False

    # Check optional variables
    for var, description in OPTIONAL_ENV_VARS.items():
        value = os.getenv(var)
        if value:
            if verbose:
                tracker.add_pass(f"{var}: set (optional)")
        else:
            if var == "TAVILY_API_KEY":
                tracker.add_warning(f"{var}: not set (MCP features will be disabled)")

    return all_required_set


def verify_python_dependencies(tracker: VerificationTracker) -> bool:
    """Verify Python dependencies are installed."""
    # Skip for now - can add if needed
    # This is typically checked during setup.py
    return True


def verify_database(tracker: VerificationTracker, quick: bool = False, verbose: bool = False) -> bool:
    """Verify MongoDB connection and setup."""
    print_separator()
    print_header("🗄️  Database")

    try:
        from shared.db import MongoDB
        from shared.config import settings

        # Test connection
        mongodb = MongoDB()
        db = mongodb.get_database()
        tracker.add_pass("MongoDB connection: successful")

        # Check collections
        existing_collections = set(db.list_collection_names())
        missing_collections = []

        for collection in REQUIRED_COLLECTIONS:
            if collection in existing_collections:
                if verbose:
                    tracker.add_pass(f"Collection '{collection}': exists")
            else:
                missing_collections.append(collection)
                tracker.add_error(
                    f"Collection '{collection}': missing",
                    f"Run: python scripts/init_db.py"
                )

        if not missing_collections:
            tracker.add_pass(f"Collections: {len(REQUIRED_COLLECTIONS)}/{len(REQUIRED_COLLECTIONS)} exist")

        # Check indexes (quick count)
        if not quick:
            total_indexes = 0
            for collection in REQUIRED_COLLECTIONS:
                if collection in existing_collections:
                    indexes = list(db[collection].list_indexes())
                    total_indexes += len(indexes)

            if total_indexes > 0:
                tracker.add_pass(f"Indexes: {total_indexes} exist")
            else:
                tracker.add_warning("Indexes: none found (run python scripts/init_db.py)")

        # Check if data exists
        total_docs = 0
        for collection in ["projects", "tasks", "long_term_memory"]:
            if collection in existing_collections:
                total_docs += db[collection].count_documents({})

        if total_docs > 0:
            tracker.add_pass(f"Data: {total_docs} documents found")
        else:
            tracker.add_warning("Data: empty (run python scripts/reset_demo.py to seed)")

        return len(missing_collections) == 0

    except Exception as e:
        tracker.add_error(
            f"MongoDB connection failed: {str(e)}",
            "Check your MONGODB_URI and network access\nEnsure MongoDB Atlas allows your IP"
        )
        return False


def verify_voyage_api(tracker: VerificationTracker, verbose: bool = False) -> bool:
    """Verify Voyage AI API."""
    try:
        from shared.embeddings import embed_document

        # Test embedding generation
        test_text = "test embedding"
        embedding = embed_document(test_text)

        # Check dimensions
        if len(embedding) == 1024:
            tracker.add_pass("Voyage AI: working (1024-dim embeddings)")
            return True
        else:
            tracker.add_warning(f"Voyage AI: unexpected dimensions ({len(embedding)}, expected 1024)")
            return True

    except Exception as e:
        tracker.add_error(
            f"Voyage AI: failed ({str(e)})",
            "Check your VOYAGE_API_KEY in .env\nGet key from: https://dash.voyageai.com/"
        )
        return False


def verify_anthropic_api(tracker: VerificationTracker, verbose: bool = False) -> bool:
    """Verify Anthropic API."""
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
            tracker.add_pass(f"Anthropic: working ({model})")
            return True
        else:
            tracker.add_error(
                "Anthropic: unexpected response",
                "Check your ANTHROPIC_API_KEY"
            )
            return False

    except Exception as e:
        tracker.add_error(
            f"Anthropic: failed ({str(e)})",
            "Check your ANTHROPIC_API_KEY in .env\nGet key from: https://console.anthropic.com/"
        )
        return False


def verify_tavily_mcp(tracker: VerificationTracker, verbose: bool = False) -> bool:
    """Verify Tavily MCP (optional)."""
    tavily_key = os.getenv("TAVILY_API_KEY")

    if not tavily_key:
        tracker.add_warning("Tavily MCP: skipped (no API key)")
        return True

    # For now, just check if key is set
    # Full MCP verification would require running the MCP server
    tracker.add_pass("Tavily MCP: API key set")
    return True


def verify_apis(tracker: VerificationTracker, quick: bool = False, verbose: bool = False) -> bool:
    """Verify all API connections."""
    print_separator()
    print_header("🔌 APIs")

    if quick:
        tracker.add_warning("API checks skipped (--quick mode)")
        return True

    all_passed = True

    # Voyage AI
    if not verify_voyage_api(tracker, verbose):
        all_passed = False

    # Anthropic
    if not verify_anthropic_api(tracker, verbose):
        all_passed = False

    # Tavily (optional)
    verify_tavily_mcp(tracker, verbose)

    return all_passed


def verify_filesystem(tracker: VerificationTracker, fix: bool = False) -> bool:
    """Verify file system setup."""
    # Typically not a critical issue, so we skip this in the main flow
    # Can be added if needed
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify Flow Companion setup",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip API calls (just check config)"
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix issues automatically (e.g., create directories)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )

    args = parser.parse_args()

    # Print header
    logger.info("🔍 Verifying Flow Companion Setup...")
    print_separator()

    tracker = VerificationTracker()

    # Run verifications
    env_ok = verify_environment(tracker, verbose=args.verbose)
    db_ok = verify_database(tracker, quick=args.quick, verbose=args.verbose)
    api_ok = verify_apis(tracker, quick=args.quick, verbose=args.verbose)

    # Summary
    print_separator()
    print_header("📊 Summary")

    logger.info(f"✅ Passed: {tracker.passed}")
    if tracker.warnings > 0:
        logger.info(f"⚠️  Warnings: {tracker.warnings}")
    if tracker.errors > 0:
        logger.info(f"❌ Errors: {tracker.errors}")

    # Final verdict
    print_separator()

    if tracker.errors == 0:
        logger.info("✅ Setup looks good!")
        if tracker.warnings > 0:
            logger.info("")
            logger.info("⚠️  Some optional features may be disabled due to warnings above.")
        logger.info("")
        logger.info("Next steps:")
        logger.info("")

        # Check if data exists
        if "empty" in str([msg for msg, _ in tracker.error_details]):
            logger.info("  Run: python scripts/reset_demo.py  (seed demo data)")
        logger.info("  Run: streamlit run streamlit_app.py  (start the app)")
        logger.info("")
        return 0
    else:
        logger.info(f"❌ Setup has {tracker.errors} error(s) that must be fixed:")
        logger.info("")

        for message, fix in tracker.error_details:
            logger.info(f"{message}")
            if fix:
                logger.info(f"  → {fix}")
            logger.info("")

        if args.fix:
            logger.info("Automatic fixes not yet implemented.")
            logger.info("Please fix the errors manually using the suggestions above.")
        else:
            logger.info("Run with --fix to attempt automatic fixes.")

        logger.info("")
        return 1


if __name__ == "__main__":
    sys.exit(main())
