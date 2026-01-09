#!/usr/bin/env python3
"""
Demo Reset Script for Flow Companion

A comprehensive setup/teardown script for demo preparation that provides
a clean, verified state for presentations.

Features:
    - TEARDOWN: Clear all demo-related collections
    - SETUP: Seed fresh demo data via seed_demo_data.py
    - VERIFY: Confirm clean state with collection counts

Usage:
    # Full reset (teardown + setup + verify)
    python scripts/reset_demo.py

    # Just clear collections
    python scripts/reset_demo.py --teardown-only

    # Just verify current state
    python scripts/reset_demo.py --verify-only

    # Skip confirmation prompts
    python scripts/reset_demo.py --force

    # Dry run (show what would be deleted)
    python scripts/reset_demo.py --dry-run

Examples:
    # Night before demo: Full reset
    python scripts/reset_demo.py --force

    # Quick check before demo
    python scripts/reset_demo.py --verify-only

    # See what will be cleared without doing it
    python scripts/reset_demo.py --dry-run

Requires:
    - .env file with MongoDB credentials
    - Virtual environment activated
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.db import MongoDB
from shared.config import settings

# We'll call seed_demo_data as subprocess instead of importing
import subprocess

# =============================================================================
# CONFIGURATION
# =============================================================================

# Collections to clear during teardown
COLLECTIONS_TO_CLEAR = [
    "projects",
    "tasks",
    "working_memory",
    "long_term_memory",
    "shared_memory",
    "tool_discoveries",
    "knowledge_cache",  # If separate collection
]

# Demo user ID (should match seed_demo_data.py)
DEMO_USER_ID = "demo-user"

# =============================================================================
# TEARDOWN
# =============================================================================

def clear_collections(db_instance, dry_run: bool = False) -> Dict[str, int]:
    """
    Clear all demo-related collections.

    Args:
        db_instance: MongoDB database instance (from get_database())
        dry_run: If True, count but don't delete

    Returns:
        Dictionary of collection names to counts deleted
    """
    results = {}

    print("\n🗑️  Clearing collections...\n")

    for collection_name in COLLECTIONS_TO_CLEAR:
        try:
            collection = db_instance[collection_name]

            # Count documents
            count = collection.count_documents({})

            if count == 0:
                print(f"  {collection_name}: already empty")
                results[collection_name] = 0
                continue

            if dry_run:
                print(f"  {collection_name}: {count} would be deleted")
                results[collection_name] = count
            else:
                # Delete all documents
                result = collection.delete_many({})
                deleted = result.deleted_count
                print(f"  {collection_name}: {deleted} deleted")
                results[collection_name] = deleted

        except Exception as e:
            print(f"  ⚠️  {collection_name}: Error - {e}")
            results[collection_name] = 0

    if dry_run:
        print("\n💡 This was a dry run - no data was deleted")
    else:
        print(f"\n✅ Cleared {len(results)} collections")

    return results

# =============================================================================
# SETUP
# =============================================================================

def seed_data(skip_embeddings: bool = False) -> bool:
    """
    Seed demo data by calling seed_demo_data.py script.

    Args:
        skip_embeddings: Skip generating embeddings for speed

    Returns:
        True if seeding succeeded, False otherwise
    """
    print("\n🌱 Seeding demo data...\n")

    try:
        # Build command
        script_path = Path(__file__).parent / "seed_demo_data.py"
        cmd = [sys.executable, str(script_path)]

        if skip_embeddings:
            cmd.append("--skip-embeddings")

        # Run seed script (clean=False since we already cleared)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        # Print output
        if result.stdout:
            print(result.stdout)

        if result.returncode != 0:
            if result.stderr:
                print(result.stderr)
            return False

        return True

    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# VERIFICATION
# =============================================================================

def verify_state(db_instance) -> bool:
    """
    Verify the demo state is ready.

    Checks:
        - GTM Roadmap Template exists in procedural memory
        - Project Alpha exists with tasks
        - Expected collection counts

    Args:
        db_instance: MongoDB database instance (from get_database())

    Returns:
        True if verification passed, False otherwise
    """
    print("\n✅ Verification:\n")

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
            print("  ✓ GTM Roadmap Template: EXISTS")
        else:
            print("  ✗ GTM Roadmap Template: MISSING")
            all_passed = False

    except Exception as e:
        print(f"  ✗ GTM Roadmap Template: Error checking - {e}")
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
            print(f"  ✓ Project Alpha: EXISTS ({task_count} tasks)")
        else:
            print("  ✗ Project Alpha: MISSING")
            all_passed = False

    except Exception as e:
        print(f"  ✗ Project Alpha: Error checking - {e}")
        all_passed = False

    # Check Q3 Fintech GTM (completed demo project)
    try:
        q3_gtm = db_instance.projects.find_one({
            "user_id": DEMO_USER_ID,
            "name": "Q3 Fintech GTM"
        })

        if q3_gtm:
            print("  ✓ Q3 Fintech GTM: EXISTS (completed)")
        else:
            print("  ℹ️  Q3 Fintech GTM: Not found (optional)")

    except Exception as e:
        print(f"  ⚠️  Q3 Fintech GTM: Error checking - {e}")

    # Print collection counts
    print("\n📊 Collection Counts:\n")

    for collection_name in COLLECTIONS_TO_CLEAR:
        try:
            count = db_instance[collection_name].count_documents({})
            if count > 0:
                print(f"  {collection_name}: {count}")
        except Exception as e:
            print(f"  {collection_name}: Error - {e}")

    # Final status
    print()
    if all_passed:
        print("🎬 Ready for demo!")
        return True
    else:
        print("⚠️  Verification failed - some issues detected")
        return False

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Reset demo environment for Flow Companion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/reset_demo.py                  # Full reset
  python scripts/reset_demo.py --force          # Skip confirmation
  python scripts/reset_demo.py --teardown-only  # Just clear
  python scripts/reset_demo.py --verify-only    # Just verify
  python scripts/reset_demo.py --dry-run        # Show what would happen
        """
    )

    parser.add_argument(
        "--teardown-only",
        action="store_true",
        help="Only clear collections, don't seed"
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
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without doing it"
    )

    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip generating embeddings (faster seeding)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Flow Companion - Demo Reset Script")
    print("=" * 60)

    # Connect to MongoDB
    try:
        print(f"\n📡 Connecting to MongoDB...")
        print(f"   Database: {settings.mongodb_database}")

        mongodb = MongoDB()
        db = mongodb.get_database()

        print(f"✓ Connected successfully")

        # Check if collections exist
        existing_collections = set(db.list_collection_names())
        missing_collections = set(COLLECTIONS_TO_CLEAR) - existing_collections

        if missing_collections and not args.verify_only:
            print(f"\n⚠️  WARNING: Some collections don't exist yet:")
            for collection in sorted(missing_collections):
                print(f"  - {collection}")

            print(f"\n💡 This might be a new database. Consider running:")
            print(f"   python scripts/init_db.py")
            print(f"\n   Or continue anyway (collections will be created during seeding).")

            if not args.force and not args.dry_run:
                response = input("\nContinue anyway? (yes/no) [yes]: ").strip().lower()
                if response in ["no", "n"]:
                    print("❌ Aborted")
                    return 1

    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # VERIFY ONLY MODE
    if args.verify_only:
        verify_state(db)
        return 0

    # CONFIRM (unless --force or --dry-run)
    if not args.force and not args.dry_run:
        print("\n⚠️  WARNING: This will DELETE all data in the following collections:")
        for collection in COLLECTIONS_TO_CLEAR:
            print(f"  - {collection}")

        response = input("\nContinue? (yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            print("❌ Aborted")
            return 1

    # TEARDOWN
    clear_results = clear_collections(db, dry_run=args.dry_run)

    if args.dry_run:
        print("\n💡 Dry run complete - no changes made")
        return 0

    # TEARDOWN ONLY MODE
    if args.teardown_only:
        print("\n✅ Teardown complete")
        return 0

    # SETUP
    seed_success = seed_data(skip_embeddings=args.skip_embeddings)

    if not seed_success:
        print("\n❌ Seeding failed")
        return 1

    # VERIFY
    verified = verify_state(db)

    if not verified:
        print("\n⚠️  Reset complete but verification found issues")
        return 1

    print("\n" + "=" * 60)
    print("✅ Demo reset complete!")
    print("=" * 60)

    print("\n💡 Next steps:")
    print("   1. Review verification results above")
    print("   2. (Optional) Run full verification: python scripts/verify_setup.py")
    print("   3. Start app: streamlit run streamlit_app.py")
    print("   4. Use demo user: demo-user")

    return 0

if __name__ == "__main__":
    sys.exit(main())
