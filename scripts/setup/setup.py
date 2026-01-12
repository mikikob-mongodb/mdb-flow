#!/usr/bin/env python3
"""
Complete First-Time Setup Script for Flow Companion.

This is the ONE command a new developer runs after cloning the repo.

It orchestrates all setup steps in order:
    1. Pre-flight checks (environment variables)
    2. Initialize database (collections + indexes)
    3. Seed demo data
    4. Verify setup (health checks)
    5. Success message with next steps

Usage:
    # Full first-time setup
    python scripts/setup.py

    # Initialize DB but don't seed data
    python scripts/setup.py --skip-seed

    # Re-run even if already set up
    python scripts/setup.py --force
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import functions from other scripts
sys.path.insert(0, str(Path(__file__).parent))

# =============================================================================
# CONFIGURATION
# =============================================================================

REQUIRED_ENV_VARS = [
    "ANTHROPIC_API_KEY",
    "VOYAGE_API_KEY",
    "OPENAI_API_KEY",
    "MONGODB_URI",
    "MONGODB_DATABASE"
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# UTILITIES
# =============================================================================

def print_long_separator():
    """Print long visual separator."""
    logger.info("━" * 67)


def print_header(text: str):
    """Print section header with separators."""
    print_long_separator()
    logger.info(text)
    print_long_separator()


def print_step(step: int, total: int, text: str):
    """Print step header."""
    logger.info(f"Step {step}/{total}: {text}")


# =============================================================================
# STEP 1: PRE-FLIGHT CHECKS
# =============================================================================

def check_environment() -> bool:
    """Check .env file and required variables."""
    print_step(1, 4, "Checking environment...")

    # Load .env file
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"

    if not env_file.exists():
        logger.error("❌ .env file not found")
        logger.error("")
        logger.error("To fix:")
        logger.error(f"  1. Copy .env.example to .env")
        logger.error(f"  2. Edit .env and add your API keys")
        logger.error(f"  3. Run this script again")
        logger.error("")
        logger.error("Required variables:")
        for var in REQUIRED_ENV_VARS:
            logger.error(f"  - {var}")
        return False

    logger.info("✅ .env file found")
    load_dotenv(env_file)

    # Check required variables
    missing = []
    for var in REQUIRED_ENV_VARS:
        value = os.getenv(var)
        if not value:
            missing.append(var)

    if missing:
        logger.error("❌ Missing required environment variables:")
        for var in missing:
            logger.error(f"  - {var}")
        logger.error("")
        logger.error(f"Edit {env_file} and add the missing variables")
        return False

    logger.info("✅ Required variables set")
    return True


# =============================================================================
# STEP 2: INITIALIZE DATABASE
# =============================================================================

def initialize_database(force: bool = False) -> bool:
    """Initialize MongoDB database."""
    print_step(2, 4, "Initializing database...")

    try:
        from shared.db import MongoDB
        from init_db import (
            COLLECTIONS,
            create_collections,
            create_tasks_indexes,
            create_projects_indexes,
            create_settings_indexes,
            create_memory_indexes,
            create_tool_discoveries_indexes,
            create_eval_indexes
        )

        # Connect to MongoDB
        mongodb = MongoDB()
        db = mongodb.get_database()
        logger.info("✅ Connected to MongoDB")

        # Create collections
        collection_results = create_collections(db, verify_only=False)
        collections_count = sum(1 for status in collection_results.values() if status in ["exists", "created"])
        logger.info(f"✅ Collections created ({collections_count})")

        # Create indexes (suppress verbose output)
        create_tasks_indexes(db, verify_only=False)
        create_projects_indexes(db, verify_only=False)
        create_settings_indexes(db, verify_only=False)
        create_memory_indexes(db, verify_only=False)
        create_tool_discoveries_indexes(db, verify_only=False)
        create_eval_indexes(db, verify_only=False)

        # Count total indexes
        total_indexes = 0
        for collection in COLLECTIONS.keys():
            indexes = list(db[collection].list_indexes())
            total_indexes += len(indexes)

        logger.info(f"✅ Indexes created ({total_indexes})")

        return True

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.error("")
        logger.error("Check:")
        logger.error("  - MONGODB_URI is correct in .env")
        logger.error("  - MongoDB Atlas allows your IP address")
        logger.error("  - Network connection is working")
        return False


# =============================================================================
# STEP 3: SEED DEMO DATA
# =============================================================================

def seed_demo_data(skip: bool = False) -> bool:
    """Seed demo data."""
    print_step(3, 4, "Seeding demo data...")

    if skip:
        logger.info("⏭️  Skipped (--skip-seed)")
        return True

    try:
        from shared.db import MongoDB
        from scripts.demo import seed_demo_data

        # Suppress verbose output
        import io
        import contextlib

        mongodb = MongoDB()
        db = mongodb.get_database()

        stdout_buffer = io.StringIO()

        with contextlib.redirect_stdout(stdout_buffer):
            # Seed all data
            projects = seed_demo_data.seed_projects(db, clean=False)
            tasks = seed_demo_data.seed_tasks(db, clean=False)
            procedural = seed_demo_data.seed_procedural_memory(db, skip_embeddings=False, clean=False)
            semantic = seed_demo_data.seed_semantic_memory(db, clean=False)
            episodic = seed_demo_data.seed_episodic_memory(db, skip_embeddings=False, clean=False)

        logger.info(f"✅ Projects: {projects}")
        logger.info(f"✅ Tasks: {tasks}")
        logger.info(f"✅ Memory entries: {procedural + semantic + episodic}")

        # Count embeddings
        embeddings_count = db.long_term_memory.count_documents({
            "user_id": "demo-user",
            "embedding": {"$exists": True}
        })
        logger.info(f"✅ Embeddings generated: {embeddings_count}")

        return True

    except Exception as e:
        logger.error(f"❌ Demo data seeding failed: {e}")
        logger.error("")
        logger.error("This is not critical - you can seed data later:")
        logger.error("  python scripts/reset_demo.py")
        logger.error("")
        logger.error("Continuing with verification...")
        return False  # Non-critical, continue


# =============================================================================
# STEP 4: VERIFY SETUP
# =============================================================================

def verify_setup() -> Dict[str, bool]:
    """Verify setup is working."""
    print_step(4, 4, "Verifying setup...")

    results = {}

    # Database check
    try:
        from shared.db import MongoDB
        mongodb = MongoDB()
        db = mongodb.get_database()
        db.list_collection_names()
        logger.info("✅ Database: OK")
        results["database"] = True
    except Exception as e:
        logger.error(f"❌ Database: FAILED ({e})")
        results["database"] = False

    # Voyage AI check
    try:
        from shared.embeddings import embed_document
        embedding = embed_document("test")
        if len(embedding) == 1024:
            logger.info("✅ Voyage AI: OK")
            results["voyage"] = True
        else:
            logger.error(f"⚠️  Voyage AI: unexpected dimensions ({len(embedding)})")
            results["voyage"] = False
    except Exception as e:
        logger.error(f"❌ Voyage AI: FAILED ({e})")
        results["voyage"] = False

    # Anthropic check
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'ok'"}]
        )
        if response.content:
            logger.info("✅ Anthropic: OK")
            results["anthropic"] = True
        else:
            logger.error("❌ Anthropic: FAILED")
            results["anthropic"] = False
    except Exception as e:
        logger.error(f"❌ Anthropic: FAILED ({e})")
        results["anthropic"] = False

    # Tavily check (optional)
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        logger.info("✅ Tavily: configured")
        results["tavily"] = True
    else:
        logger.info("⚠️  Tavily: not configured (optional)")
        results["tavily"] = None  # Optional, not a failure

    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Complete first-time setup for Flow Companion",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Initialize DB but don't seed demo data"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run even if already set up"
    )

    args = parser.parse_args()

    # Print header
    print_header("🚀 Flow Companion - First Time Setup")

    # Step 1: Pre-flight checks
    if not check_environment():
        return 1

    # Step 2: Initialize database
    if not initialize_database(force=args.force):
        return 1

    # Step 3: Seed demo data
    seed_success = seed_demo_data(skip=args.skip_seed)

    # Step 4: Verify setup
    results = verify_setup()

    # Summary
    print_long_separator()

    # Check if all critical components passed
    critical_passed = all([
        results.get("database", False),
        results.get("voyage", False),
        results.get("anthropic", False)
    ])

    if critical_passed:
        logger.info("✅ Setup Complete!")
        print_long_separator()
        logger.info("")
        logger.info("To start the app:")
        logger.info("  streamlit run streamlit_app.py")
        logger.info("")
        logger.info("To reset demo data later:")
        logger.info("  python scripts/reset_demo.py")
        logger.info("")
        logger.info("To verify setup:")
        logger.info("  python scripts/verify_setup.py")
        logger.info("")
        return 0
    else:
        logger.error("❌ Setup incomplete - some checks failed")
        print_long_separator()
        logger.error("")
        logger.error("Failed components:")
        if not results.get("database"):
            logger.error("  - Database (check MONGODB_URI)")
        if not results.get("voyage"):
            logger.error("  - Voyage AI (check VOYAGE_API_KEY)")
        if not results.get("anthropic"):
            logger.error("  - Anthropic (check ANTHROPIC_API_KEY)")
        logger.error("")
        logger.error("Fix the issues above and run again:")
        logger.error("  python scripts/setup.py")
        logger.error("")
        return 1


if __name__ == "__main__":
    sys.exit(main())
