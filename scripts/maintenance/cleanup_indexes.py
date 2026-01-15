#!/usr/bin/env python3
"""
MongoDB Index Cleanup Script

Removes redundant indexes identified in index-dependency-analysis.md
Supports dry-run mode and phased cleanup.

Usage:
    python scripts/maintenance/cleanup_indexes.py --dry-run              # Show what would be removed
    python scripts/maintenance/cleanup_indexes.py --phase 1              # Remove Phase 1 indexes (memory_long_term)
    python scripts/maintenance/cleanup_indexes.py --phase 2              # Remove Phase 1 + Phase 2 indexes
    python scripts/maintenance/cleanup_indexes.py --phase 1 --force      # Skip confirmations
"""

import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pymongo import MongoClient
from dotenv import load_dotenv
from shared.logger import get_logger

logger = get_logger("cleanup_indexes")

# Load environment
load_dotenv()

# =============================================================================
# INDEX REMOVAL DEFINITIONS
# =============================================================================

PHASE_1_REMOVALS = {
    "memory_long_term": [
        "type_1",                           # Covered by compounds (memory_type)
        "user_timestamp_index",             # Redundant - basic user+timestamp
        "user_category_timestamp_index",    # Redundant - rarely used
        "user_type_timestamp_index",        # Redundant - rarely used
    ]
}

PHASE_2_REMOVALS = {
    "tasks": [
        "idx_status",                       # Low cardinality, covered by idx_project_status
        "idx_priority",                     # Low cardinality, covered by idx_status_priority
    ],
    "projects": [
        "idx_status",                       # Low cardinality, covered by idx_user_status
    ],
    "memory_shared": [
        "from_agent_1",                     # Covered by compounds
        "to_agent_1",                       # Covered by compounds
        "status_1",                         # Covered by session_id_1_target_agent_1_status_1
    ]
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_db_connection():
    """Get MongoDB connection."""
    mongodb_uri = os.getenv("MONGODB_URI")
    mongodb_database = os.getenv("MONGODB_DATABASE", "flow_companion")

    if not mongodb_uri:
        logger.error("MONGODB_URI not found in environment")
        sys.exit(1)

    try:
        client = MongoClient(mongodb_uri)
        db = client[mongodb_database]
        # Test connection
        db.command("ping")
        logger.info(f"✅ Connected to MongoDB: {mongodb_database}")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)

def get_existing_indexes(db, collection_name):
    """Get list of existing index names for a collection."""
    try:
        collection = db[collection_name]
        indexes = collection.list_indexes()
        return [idx['name'] for idx in indexes]
    except Exception as e:
        logger.warning(f"Failed to list indexes for {collection_name}: {e}")
        return []

def backup_indexes(db, output_file="index_backup.json"):
    """Backup all indexes to JSON file."""
    backup = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": db.name,
        "collections": {}
    }

    collections = ["memory_long_term", "tasks", "projects", "memory_short_term", "memory_shared", "tool_discoveries"]

    for coll_name in collections:
        try:
            coll = db[coll_name]
            indexes = list(coll.list_indexes())
            backup["collections"][coll_name] = indexes
        except Exception as e:
            logger.warning(f"Failed to backup indexes for {coll_name}: {e}")

    backup_path = Path(__file__).parent / output_file
    with open(backup_path, 'w') as f:
        json.dump(backup, f, indent=2, default=str)

    logger.info(f"📦 Index backup saved to: {backup_path}")
    return backup_path

def remove_index(db, collection_name, index_name, dry_run=False):
    """Remove a single index."""
    if dry_run:
        logger.info(f"  [DRY RUN] Would remove: {collection_name}.{index_name}")
        return True

    try:
        collection = db[collection_name]
        collection.drop_index(index_name)
        logger.info(f"  ✅ Removed: {collection_name}.{index_name}")
        return True
    except Exception as e:
        logger.error(f"  ❌ Failed to remove {collection_name}.{index_name}: {e}")
        return False

def print_removal_plan(phase, dry_run=False):
    """Print what will be removed."""
    mode = "DRY RUN - " if dry_run else ""
    logger.info("")
    logger.info(f"{'='*70}")
    logger.info(f"{mode}Phase {phase} Index Removal Plan")
    logger.info(f"{'='*70}")

    removals = PHASE_1_REMOVALS.copy()
    if phase >= 2:
        removals.update(PHASE_2_REMOVALS)

    total_count = sum(len(indexes) for indexes in removals.values())

    for collection, indexes in removals.items():
        logger.info(f"\n{collection}: ({len(indexes)} indexes)")
        for idx in indexes:
            logger.info(f"  ❌ {idx}")

    logger.info(f"\n{'='*70}")
    logger.info(f"Total indexes to remove: {total_count}")
    logger.info(f"{'='*70}")
    logger.info("")

def verify_compounds_exist(db, collection_name, required_compounds):
    """Verify that required compound indexes exist before removing single-field indexes."""
    existing = get_existing_indexes(db, collection_name)
    missing = [comp for comp in required_compounds if comp not in existing]

    if missing:
        logger.warning(f"⚠️  Missing compound indexes in {collection_name}: {missing}")
        logger.warning(f"   Single-field index removal may impact query performance!")
        return False
    return True

def run_cleanup(db, phase, dry_run=False, force=False):
    """Execute index cleanup."""

    # Print plan
    print_removal_plan(phase, dry_run)

    # Confirmation (unless force or dry-run)
    if not dry_run and not force:
        logger.info("⚠️  This will permanently remove indexes from your database.")
        response = input("Continue? (yes/no): ").strip().lower()
        if response != "yes":
            logger.info("Cleanup cancelled.")
            return

    # Backup indexes (unless dry-run)
    if not dry_run:
        backup_path = backup_indexes(db)
        logger.info(f"Backup created at: {backup_path}")
        logger.info("")

    # Get removals for selected phase
    removals = PHASE_1_REMOVALS.copy()
    if phase >= 2:
        removals.update(PHASE_2_REMOVALS)

    # Verify compound indexes exist (Phase 1 only for now)
    if phase >= 1:
        required_long_term = [
            "user_id_1_action_type_1",
            "user_id_1_source_agent_1",
            "user_id_1_memory_type_1_semantic_type_1_key_1",  # semantic_lookup
            "user_id_1_memory_type_1_trigger_pattern_1",      # procedural_lookup
        ]
        if not verify_compounds_exist(db, "memory_long_term", required_long_term):
            logger.error("❌ Required compound indexes not found!")
            logger.error("   Run 'python scripts/setup/init_db.py' to create missing indexes.")
            if not force:
                sys.exit(1)

    # Verify compound indexes for Phase 2
    if phase >= 2:
        required_tasks = ["idx_project_status", "idx_status_priority"]
        required_projects = ["idx_user_status"]
        required_shared = ["session_id_1_target_agent_1_status_1"]

        all_ok = True
        all_ok &= verify_compounds_exist(db, "tasks", required_tasks)
        all_ok &= verify_compounds_exist(db, "projects", required_projects)
        all_ok &= verify_compounds_exist(db, "memory_shared", required_shared)

        if not all_ok and not force:
            logger.error("❌ Required compound indexes not found!")
            sys.exit(1)

    # Execute removals
    stats = {
        "attempted": 0,
        "succeeded": 0,
        "failed": 0,
        "skipped": 0
    }

    for collection_name, index_names in removals.items():
        logger.info(f"\nProcessing {collection_name}...")
        existing_indexes = get_existing_indexes(db, collection_name)

        for index_name in index_names:
            stats["attempted"] += 1

            # Check if index exists
            if index_name not in existing_indexes:
                logger.info(f"  ⏭️  Skipped: {index_name} (not found)")
                stats["skipped"] += 1
                continue

            # Remove index
            if remove_index(db, collection_name, index_name, dry_run):
                stats["succeeded"] += 1
            else:
                stats["failed"] += 1

    # Summary
    logger.info("")
    logger.info(f"{'='*70}")
    logger.info("Cleanup Summary")
    logger.info(f"{'='*70}")
    logger.info(f"Attempted:  {stats['attempted']}")
    logger.info(f"Succeeded:  {stats['succeeded']}")
    logger.info(f"Failed:     {stats['failed']}")
    logger.info(f"Skipped:    {stats['skipped']}")
    logger.info(f"{'='*70}")

    if not dry_run and stats["succeeded"] > 0:
        logger.info("")
        logger.info("✅ Index cleanup complete!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Monitor query performance for 24-48 hours")
        logger.info("  2. Check slow query logs")
        logger.info("  3. Verify write latency improvements")
        logger.info("  4. Update init_db.py to remove index definitions")
        logger.info("")
        logger.info(f"To restore indexes, use: mongorestore with {backup_path}")

def list_current_indexes(db):
    """List all current indexes."""
    collections = ["memory_long_term", "tasks", "projects", "memory_short_term", "memory_shared"]

    logger.info("")
    logger.info(f"{'='*70}")
    logger.info("Current Index Status")
    logger.info(f"{'='*70}")

    total = 0
    for coll_name in collections:
        indexes = get_existing_indexes(db, coll_name)
        logger.info(f"\n{coll_name}: ({len(indexes)} indexes)")
        for idx in indexes:
            logger.info(f"  • {idx}")
        total += len(indexes)

    logger.info(f"\n{'='*70}")
    logger.info(f"Total indexes: {total}")
    logger.info(f"{'='*70}")

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Clean up redundant MongoDB indexes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show what would be removed (Phase 1)
  python scripts/maintenance/cleanup_indexes.py --dry-run --phase 1

  # Remove Phase 1 indexes (memory_long_term only)
  python scripts/maintenance/cleanup_indexes.py --phase 1

  # Remove Phase 1 + Phase 2 indexes
  python scripts/maintenance/cleanup_indexes.py --phase 2

  # Force removal without confirmation
  python scripts/maintenance/cleanup_indexes.py --phase 1 --force

  # List current indexes
  python scripts/maintenance/cleanup_indexes.py --list

Phase 1 (8 indexes from memory_long_term):
  - Removes single-field indexes covered by compounds
  - Recommended first step

Phase 2 (3 additional indexes from tasks and projects):
  - Removes low-cardinality indexes
  - Requires validation after Phase 1
        """
    )

    parser.add_argument("--phase", type=int, choices=[1, 2], default=1,
                       help="Cleanup phase (1=memory_long_term, 2=all)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be removed without executing")
    parser.add_argument("--force", action="store_true",
                       help="Skip confirmation prompts")
    parser.add_argument("--list", action="store_true",
                       help="List current indexes and exit")

    args = parser.parse_args()

    # Connect to database
    db = get_db_connection()

    # List mode
    if args.list:
        list_current_indexes(db)
        return 0

    # Run cleanup
    run_cleanup(db, args.phase, args.dry_run, args.force)

    return 0

if __name__ == "__main__":
    sys.exit(main())
