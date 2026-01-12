#!/usr/bin/env python3
"""
Demo Reset Script for Flow Companion

A comprehensive setup/teardown script for demo preparation that provides
a clean, verified state for presentations.

Features:
    - TEARDOWN: Clear all demo-related collections
    - SETUP: Seed fresh demo data
    - VERIFY: Confirm clean state with validation

Usage:
    # Full reset (teardown + setup + verify)
    python scripts/reset_demo.py

    # Just clear collections (requires --force)
    python scripts/reset_demo.py --teardown-only --force

    # Just seed (no teardown)
    python scripts/reset_demo.py --seed-only

    # Just verify current state
    python scripts/reset_demo.py --verify-only

    # Skip embeddings (faster)
    python scripts/reset_demo.py --skip-embeddings

Examples:
    # Night before demo: Full reset
    python scripts/reset_demo.py

    # Quick check before demo
    python scripts/reset_demo.py --verify-only

Safety:
    - Detects production URIs and requires extra confirmation
    - Requires --force flag for --teardown-only
    - Always shows what will be deleted before proceeding

Requires:
    - .env file with MongoDB credentials
    - Virtual environment activated
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.db import MongoDB
from shared.config import settings

# Import seeding functions from same directory
sys.path.insert(0, str(Path(__file__).parent))
import seed_demo_data

# =============================================================================
# CONFIGURATION
# =============================================================================

# Collections to clear during teardown
COLLECTIONS_TO_CLEAR = [
    "projects",
    "tasks",
    "short_term_memory",
    "long_term_memory",
    "shared_memory",
    "tool_discoveries",
]

# Demo user ID (must match seed_demo_data.py)
DEMO_USER_ID = "demo-user"

# Production URI keywords
PRODUCTION_KEYWORDS = ["production", "prod", "live"]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# SAFETY CHECKS
# =============================================================================

def is_production_database() -> bool:
    """Check if the MongoDB URI appears to be for production."""
    uri = settings.mongodb_uri.lower()
    db_name = settings.mongodb_database.lower()

    for keyword in PRODUCTION_KEYWORDS:
        if keyword in uri or keyword in db_name:
            return True

    return False


def confirm_production_reset() -> bool:
    """Extra confirmation for production database reset."""
    logger.warning("⚠️  WARNING: This appears to be a PRODUCTION database!")
    logger.warning(f"   Database: {settings.mongodb_database}")
    logger.warning(f"   This will DELETE ALL DATA in the collections listed above.")
    logger.warning("")

    response = input("Type 'DELETE PRODUCTION DATA' to confirm: ").strip()

    if response == "DELETE PRODUCTION DATA":
        logger.info("✓ Confirmed")
        return True
    else:
        logger.error("❌ Confirmation failed - aborted")
        return False


# =============================================================================
# TEARDOWN
# =============================================================================

def teardown(db_instance, dry_run: bool = False) -> Dict[str, int]:
    """
    Clear all demo-related collections.

    Args:
        db_instance: MongoDB database instance
        dry_run: If True, count but don't delete

    Returns:
        Dictionary of collection names to counts deleted
    """
    logger.info("🗑️  Teardown:")
    logger.info("")

    results = {}
    total_deleted = 0

    for collection_name in COLLECTIONS_TO_CLEAR:
        try:
            collection = db_instance[collection_name]

            # Count documents
            count = collection.count_documents({})

            if count == 0:
                # Skip empty collections in output
                results[collection_name] = 0
                continue

            if dry_run:
                logger.info(f"  {collection_name}: {count} would be deleted")
                results[collection_name] = count
            else:
                # Delete all documents
                result = collection.delete_many({})
                deleted = result.deleted_count
                logger.info(f"  {collection_name}: {deleted} deleted")
                results[collection_name] = deleted
                total_deleted += deleted

        except Exception as e:
            logger.warning(f"  ⚠️  {collection_name}: Error - {e}")
            results[collection_name] = 0

    logger.info("")

    if dry_run:
        logger.info("💡 Dry run - no data was deleted")

    return results


# =============================================================================
# SETUP
# =============================================================================

def setup(db_instance, skip_embeddings: bool = False) -> Dict[str, int]:
    """
    Seed demo data by calling seed_demo_data functions.

    Args:
        db_instance: MongoDB database instance
        skip_embeddings: Skip generating embeddings for speed

    Returns:
        Dictionary of data types to counts inserted
    """
    logger.info("🌱 Seeding:")
    logger.info("")

    results = {}

    try:
        # Suppress stdout from seed functions (they use print())
        import io
        import contextlib

        stdout_buffer = io.StringIO()

        with contextlib.redirect_stdout(stdout_buffer):
            # Seed projects
            results["projects"] = seed_demo_data.seed_projects(db_instance, clean=False)

            # Seed tasks
            results["tasks"] = seed_demo_data.seed_tasks(db_instance, clean=False)

            # Seed procedural memory
            results["procedural"] = seed_demo_data.seed_procedural_memory(
                db_instance,
                skip_embeddings=skip_embeddings,
                clean=False
            )

            # Seed semantic memory
            results["semantic"] = seed_demo_data.seed_semantic_memory(db_instance, clean=False)

            # Seed episodic memory
            results["episodic"] = seed_demo_data.seed_episodic_memory(
                db_instance,
                skip_embeddings=skip_embeddings,
                clean=False
            )

        # Show summary
        logger.info(f"  projects: {results['projects']} inserted")
        logger.info(f"  tasks: {results['tasks']} inserted")
        logger.info(f"  procedural memory: {results['procedural']} inserted")
        logger.info(f"  semantic memory: {results['semantic']} inserted")
        logger.info(f"  episodic memory: {results['episodic']} inserted")

        # Count embeddings generated
        if not skip_embeddings:
            embeddings_count = db_instance.long_term_memory.count_documents({
                "user_id": DEMO_USER_ID,
                "embedding": {"$exists": True}
            })
            results["embeddings"] = embeddings_count
            logger.info(f"  embeddings: {embeddings_count} generated")
        else:
            results["embeddings"] = 0

        logger.info("")

        return results

    except Exception as e:
        logger.error(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        return {}


# =============================================================================
# VERIFICATION
# =============================================================================

def verify(db_instance) -> bool:
    """
    Verify the demo state is ready.

    Checks:
        - GTM Roadmap Template exists in procedural memory
        - Project Alpha exists with tasks
        - Q3 Fintech GTM exists (completed)
        - User preferences exist in semantic memory

    Args:
        db_instance: MongoDB database instance

    Returns:
        True if verification passed, False otherwise
    """
    logger.info("✅ Verification:")
    logger.info("")

    all_passed = True

    # Check GTM Roadmap Template
    try:
        gtm_template = db_instance.long_term_memory.find_one({
            "user_id": DEMO_USER_ID,
            "memory_type": "procedural",
            "rule_type": "template",
            "name": "GTM Roadmap Template"
        })

        if gtm_template:
            logger.info("  GTM Roadmap Template: ✅ EXISTS")
        else:
            logger.info("  GTM Roadmap Template: ❌ MISSING")
            all_passed = False

    except Exception as e:
        logger.warning(f"  GTM Roadmap Template: ⚠️  Error - {e}")
        all_passed = False

    # Check Project Alpha
    try:
        project_alpha = db_instance.projects.find_one({
            "user_id": DEMO_USER_ID,
            "name": "Project Alpha"
        })

        if project_alpha:
            # Count tasks for Project Alpha
            task_count = db_instance.tasks.count_documents({
                "user_id": DEMO_USER_ID,
                "project_id": project_alpha["_id"]
            })
            logger.info(f"  Project Alpha: ✅ EXISTS ({task_count} tasks)")
        else:
            logger.info("  Project Alpha: ❌ MISSING")
            all_passed = False

    except Exception as e:
        logger.warning(f"  Project Alpha: ⚠️  Error - {e}")
        all_passed = False

    # Check Q3 Fintech GTM (completed demo project)
    try:
        q3_gtm = db_instance.projects.find_one({
            "user_id": DEMO_USER_ID,
            "name": "Q3 Fintech GTM"
        })

        if q3_gtm:
            status = q3_gtm.get("status", "unknown")
            logger.info(f"  Q3 Fintech GTM: ✅ EXISTS ({status})")
        else:
            logger.info("  Q3 Fintech GTM: ❌ MISSING")
            all_passed = False

    except Exception as e:
        logger.warning(f"  Q3 Fintech GTM: ⚠️  Error - {e}")
        all_passed = False

    # Check User preferences in semantic memory
    try:
        preferences_count = db_instance.long_term_memory.count_documents({
            "user_id": DEMO_USER_ID,
            "memory_type": "semantic",
            "semantic_type": "preference"
        })

        if preferences_count > 0:
            logger.info(f"  User preferences: ✅ EXISTS ({preferences_count} preferences)")
        else:
            logger.info("  User preferences: ❌ MISSING")
            all_passed = False

    except Exception as e:
        logger.warning(f"  User preferences: ⚠️  Error - {e}")
        all_passed = False

    logger.info("")

    return all_passed


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Reset demo environment for Flow Companion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/reset_demo.py                      # Full reset
  python scripts/reset_demo.py --teardown-only --force  # Just clear
  python scripts/reset_demo.py --seed-only          # Just seed
  python scripts/reset_demo.py --verify-only        # Just verify
  python scripts/reset_demo.py --skip-embeddings    # Faster seeding
        """
    )

    parser.add_argument(
        "--teardown-only",
        action="store_true",
        help="Only clear collections (requires --force)"
    )

    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Only seed data, don't teardown"
    )

    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify state, don't modify anything"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts"
    )

    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip generating embeddings (faster seeding)"
    )

    args = parser.parse_args()

    # Validation: --teardown-only requires --force
    if args.teardown_only and not args.force:
        logger.error("❌ --teardown-only requires --force flag for safety")
        logger.error("   This operation will DELETE all data!")
        return 1

    # Print header
    logger.info("🔄 Resetting Flow Companion Demo Data...")
    logger.info("")

    # Connect to MongoDB
    try:
        mongodb = MongoDB()
        db = mongodb.get_database()

    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # VERIFY ONLY MODE
    if args.verify_only:
        verified = verify(db)

        if verified:
            logger.info("━" * 43)
            logger.info("🎬 Ready for demo!")
            logger.info("━" * 43)
            return 0
        else:
            logger.info("━" * 43)
            logger.info("⚠️  Some verification checks failed")
            logger.info("━" * 43)
            return 1

    # SEED ONLY MODE
    if args.seed_only:
        setup_results = setup(db, skip_embeddings=args.skip_embeddings)

        if setup_results:
            logger.info("")
            verified = verify(db)

            if verified:
                logger.info("━" * 43)
                logger.info("🎬 Ready for demo!")
                logger.info("━" * 43)
                return 0
            else:
                logger.info("━" * 43)
                logger.info("⚠️  Seeding complete but verification failed")
                logger.info("━" * 43)
                return 1
        else:
            logger.error("❌ Seeding failed")
            return 1

    # FULL RESET OR TEARDOWN ONLY

    # Safety check for production
    if is_production_database():
        if not confirm_production_reset():
            return 1

    # Confirm (unless --force)
    if not args.force:
        logger.warning("⚠️  WARNING: This will DELETE all data in the following collections:")
        for collection in COLLECTIONS_TO_CLEAR:
            logger.warning(f"  - {collection}")
        logger.warning("")

        response = input("Continue? (yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            logger.error("❌ Aborted")
            return 1
        logger.info("")

    # TEARDOWN
    teardown_results = teardown(db)

    # TEARDOWN ONLY MODE
    if args.teardown_only:
        logger.info("✅ Teardown complete")
        return 0

    # SETUP
    logger.info("")
    setup_results = setup(db, skip_embeddings=args.skip_embeddings)

    if not setup_results:
        logger.error("❌ Seeding failed")
        return 1

    # VERIFY
    logger.info("")
    verified = verify(db)

    logger.info("")
    logger.info("━" * 43)

    if verified:
        logger.info("🎬 Ready for demo!")
    else:
        logger.info("⚠️  Reset complete but verification found issues")

    logger.info("━" * 43)

    return 0 if verified else 1


if __name__ == "__main__":
    sys.exit(main())
