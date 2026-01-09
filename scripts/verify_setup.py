#!/usr/bin/env python3
"""
Setup Verification Script for Flow Companion.

Performs comprehensive health checks to verify that all components are
properly configured and functioning.

Checks:
    - Environment variables (required and optional)
    - MongoDB connection and database access
    - Collections existence
    - Indexes (standard, text search, TTL, vector search)
    - API connectivity (Anthropic, Voyage, OpenAI, Tavily)
    - Basic CRUD operations

Usage:
    # Full verification (recommended)
    python scripts/verify_setup.py

    # Quick check (env + connection only)
    python scripts/verify_setup.py --quick

    # Skip API tests (faster)
    python scripts/verify_setup.py --skip-api

    # Verbose output
    python scripts/verify_setup.py --verbose
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

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

OPTIONAL_ENV_VARS = [
    "TAVILY_API_KEY",
    "MONGODB_MCP_ENABLED",
    "MCP_MODE_ENABLED",
    "LOG_LEVEL",
    "DEBUG"
]

REQUIRED_COLLECTIONS = [
    "tasks",
    "projects",
    "settings",
    "short_term_memory",
    "long_term_memory",
    "shared_memory",
    "tool_discoveries",
    "eval_comparison_runs"
]

VECTOR_INDEXES = {
    "tasks": "vector_index",
    "projects": "vector_index",
    "long_term_memory": ["memory_embeddings", "vector_index"],  # Has two
    "tool_discoveries": "discovery_vector_index"
}

# =============================================================================
# VERIFICATION RESULTS TRACKER
# =============================================================================

class VerificationResults:
    """Track verification results across all checks."""

    def __init__(self):
        self.results = {
            "environment": {},
            "mongodb": {},
            "collections": {},
            "indexes": {},
            "apis": {},
            "operations": {}
        }
        self.warnings = []
        self.errors = []

    def add_check(self, category: str, name: str, passed: bool, message: str = ""):
        """Add a check result."""
        self.results[category][name] = {
            "passed": passed,
            "message": message
        }
        if not passed:
            self.errors.append(f"{category}.{name}: {message}")

    def add_warning(self, message: str):
        """Add a warning."""
        self.warnings.append(message)

    def print_summary(self):
        """Print verification summary."""
        print("\n" + "="*70)
        print("VERIFICATION SUMMARY")
        print("="*70)

        total_checks = sum(len(checks) for checks in self.results.values())
        passed_checks = sum(
            1 for checks in self.results.values()
            for check in checks.values()
            if check["passed"]
        )

        print(f"\n✓ Passed: {passed_checks}/{total_checks} checks")

        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings[:5]:  # Show first 5
                print(f"    - {warning}")
            if len(self.warnings) > 5:
                print(f"    ... and {len(self.warnings) - 5} more")

        if self.errors:
            print(f"\n✗ Errors: {len(self.errors)}")
            for error in self.errors[:5]:  # Show first 5
                print(f"    - {error}")
            if len(self.errors) > 5:
                print(f"    ... and {len(self.errors) - 5} more")

        print("\n" + "="*70)
        if not self.errors:
            print("✅ ALL CHECKS PASSED - Setup is ready!")
        else:
            print("❌ SOME CHECKS FAILED - See errors above")
        print("="*70)

        return len(self.errors) == 0

# =============================================================================
# ENVIRONMENT CHECKS
# =============================================================================

def verify_environment(results: VerificationResults, verbose: bool = False):
    """Verify environment variables are properly configured."""

    print("\n" + "="*70)
    print("CHECKING ENVIRONMENT VARIABLES")
    print("="*70)

    # Load .env file first
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    load_dotenv(env_file)
    if env_file.exists():
        print(f"\n✓ .env file found: {env_file}")
        results.add_check("environment", "env_file_exists", True)
    else:
        print(f"\n✗ .env file NOT found: {env_file}")
        results.add_check("environment", "env_file_exists", False, ".env file missing")

    # Check required variables
    print("\n📋 Required Variables:")
    for var in REQUIRED_ENV_VARS:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "URI" in var:
                display_value = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display_value = value

            print(f"  ✓ {var}: {display_value}")
            results.add_check("environment", var, True)

            # Additional validation
            if var == "MONGODB_URI" and not value.startswith("mongodb"):
                results.add_warning(f"{var} doesn't start with 'mongodb://' or 'mongodb+srv://'")
            elif var == "ANTHROPIC_API_KEY" and not value.startswith("sk-ant-"):
                results.add_warning(f"{var} doesn't start with 'sk-ant-' (may be invalid)")
            elif var == "VOYAGE_API_KEY" and not value.startswith("pa-"):
                results.add_warning(f"{var} doesn't start with 'pa-' (may be invalid)")
            elif var == "OPENAI_API_KEY" and not value.startswith("sk-"):
                results.add_warning(f"{var} doesn't start with 'sk-' (may be invalid)")

        else:
            print(f"  ✗ {var}: NOT SET")
            results.add_check("environment", var, False, "Not set in environment")

    # Check optional variables
    print("\n📋 Optional Variables:")
    for var in OPTIONAL_ENV_VARS:
        value = os.getenv(var)
        if value:
            if "KEY" in var:
                display_value = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"  ✓ {var}: {display_value}")
        else:
            print(f"  - {var}: not set (optional)")

    # Try importing config to verify Pydantic validation
    print("\n📦 Testing config import...")
    try:
        from shared.config import settings
        print("  ✓ Config loaded successfully")
        results.add_check("environment", "config_import", True)

        # Check MCP availability
        if settings.mcp_available:
            print(f"  ✓ MCP available (Tavily: {bool(settings.tavily_api_key)})")
        else:
            print("  - MCP not available (Tavily key not set)")

    except Exception as e:
        print(f"  ✗ Config import failed: {e}")
        results.add_check("environment", "config_import", False, str(e))

# =============================================================================
# MONGODB CHECKS
# =============================================================================

def verify_mongodb(results: VerificationResults, verbose: bool = False):
    """Verify MongoDB connection and database access."""

    print("\n" + "="*70)
    print("CHECKING MONGODB CONNECTION")
    print("="*70)

    try:
        from shared.db import MongoDB
        from shared.config import settings

        print(f"\n📡 Connecting to MongoDB...")
        print(f"   Database: {settings.mongodb_database}")

        mongodb = MongoDB()
        db = mongodb.get_database()

        print("✓ Connection successful")
        results.add_check("mongodb", "connection", True)

        # Test database access
        collections = db.list_collection_names()
        print(f"✓ Database access verified ({len(collections)} collections found)")
        results.add_check("mongodb", "database_access", True)

        # Test write permission
        test_collection = db["_setup_test"]
        test_doc = {"test": True, "timestamp": datetime.now()}
        test_collection.insert_one(test_doc)
        test_collection.delete_many({"test": True})
        print("✓ Write permission verified")
        results.add_check("mongodb", "write_permission", True)

        # Check MongoDB version
        server_info = db.client.server_info()
        version = server_info.get("version", "unknown")
        print(f"✓ MongoDB version: {version}")

        if verbose:
            print(f"\n📊 Server Info:")
            print(f"   Version: {version}")
            print(f"   Collections: {len(collections)}")

        return db

    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        results.add_check("mongodb", "connection", False, str(e))
        return None

# =============================================================================
# COLLECTION CHECKS
# =============================================================================

def verify_collections(db_instance, results: VerificationResults, verbose: bool = False):
    """Verify all required collections exist."""

    if not db_instance:
        print("\n⚠️  Skipping collection checks (no database connection)")
        return

    print("\n" + "="*70)
    print("CHECKING COLLECTIONS")
    print("="*70)

    existing_collections = set(db_instance.list_collection_names())

    print("\n📦 Required Collections:")
    for collection in REQUIRED_COLLECTIONS:
        if collection in existing_collections:
            doc_count = db_instance[collection].count_documents({})
            print(f"  ✓ {collection}: exists ({doc_count} documents)")
            results.add_check("collections", collection, True)
        else:
            print(f"  ✗ {collection}: MISSING")
            results.add_check("collections", collection, False, "Collection does not exist")

    # Report any unexpected collections
    unexpected = existing_collections - set(REQUIRED_COLLECTIONS) - {"_setup_test"}
    if unexpected:
        print(f"\n📋 Additional collections found:")
        for collection in sorted(unexpected):
            print(f"  - {collection}")

# =============================================================================
# INDEX CHECKS
# =============================================================================

def verify_indexes(db_instance, results: VerificationResults, verbose: bool = False):
    """Verify indexes are created correctly."""

    if not db_instance:
        print("\n⚠️  Skipping index checks (no database connection)")
        return

    print("\n" + "="*70)
    print("CHECKING INDEXES")
    print("="*70)

    # Standard indexes
    print("\n📋 Standard Indexes:")
    for collection in ["tasks", "projects", "settings"]:
        if collection not in db_instance.list_collection_names():
            continue

        indexes = list(db_instance[collection].list_indexes())
        index_names = [idx["name"] for idx in indexes]

        # Check for key indexes
        required_indexes = {
            "tasks": ["idx_user_id", "idx_project_id", "idx_status", "idx_text_search"],
            "projects": ["idx_user_id", "idx_status", "idx_text_search"],
            "settings": ["idx_user_id"]
        }

        missing = []
        for required in required_indexes.get(collection, []):
            if required in index_names:
                if verbose:
                    print(f"  ✓ {collection}.{required}")
            else:
                missing.append(required)

        if missing:
            print(f"  ✗ {collection}: Missing indexes: {', '.join(missing)}")
            results.add_check("indexes", f"{collection}_standard", False,
                            f"Missing: {', '.join(missing)}")
        else:
            print(f"  ✓ {collection}: {len(indexes)} indexes")
            results.add_check("indexes", f"{collection}_standard", True)

    # Memory indexes
    print("\n🧠 Memory Indexes:")
    for collection in ["short_term_memory", "long_term_memory", "shared_memory"]:
        if collection not in db_instance.list_collection_names():
            continue

        indexes = list(db_instance[collection].list_indexes())
        index_names = [idx["name"] for idx in indexes]

        # Check for TTL indexes
        if collection in ["short_term_memory", "shared_memory"]:
            has_ttl = any("expires_at" in str(idx.get("key", {})) for idx in indexes)
            if has_ttl:
                print(f"  ✓ {collection}: {len(indexes)} indexes (includes TTL)")
                results.add_check("indexes", f"{collection}_ttl", True)
            else:
                print(f"  ⚠️  {collection}: No TTL index found")
                results.add_check("indexes", f"{collection}_ttl", False, "Missing TTL index")
        else:
            print(f"  ✓ {collection}: {len(indexes)} indexes")
            results.add_check("indexes", f"{collection}_standard", True)

    # Vector search indexes (check via aggregation attempt)
    print("\n🔍 Vector Search Indexes:")
    for collection, index_name in VECTOR_INDEXES.items():
        if collection not in db_instance.list_collection_names():
            continue

        # Handle multiple possible index names
        index_names = index_name if isinstance(index_name, list) else [index_name]

        for idx_name in index_names:
            try:
                # Try a vector search query to verify index exists
                import numpy as np
                test_vector = np.random.rand(1024).tolist()

                pipeline = [
                    {
                        "$vectorSearch": {
                            "index": idx_name,
                            "path": "embedding" if collection != "tool_discoveries" else "request_embedding",
                            "queryVector": test_vector,
                            "numCandidates": 1,
                            "limit": 1
                        }
                    },
                    {"$limit": 1}
                ]

                # This will fail if index doesn't exist
                list(db_instance[collection].aggregate(pipeline))
                print(f"  ✓ {collection}.{idx_name}")
                results.add_check("indexes", f"{collection}_{idx_name}", True)

            except Exception as e:
                error_msg = str(e)
                if "index not found" in error_msg.lower() or "no search index" in error_msg.lower():
                    print(f"  ✗ {collection}.{idx_name}: NOT FOUND")
                    results.add_check("indexes", f"{collection}_{idx_name}", False,
                                    "Vector search index not created in Atlas")
                else:
                    print(f"  ⚠️  {collection}.{idx_name}: Cannot verify ({error_msg[:50]}...)")
                    results.add_warning(f"Cannot verify vector index {collection}.{idx_name}")

# =============================================================================
# API CHECKS
# =============================================================================

def verify_apis(results: VerificationResults, verbose: bool = False):
    """Verify API connectivity."""

    print("\n" + "="*70)
    print("CHECKING API CONNECTIVITY")
    print("="*70)

    # Anthropic API
    print("\n🤖 Anthropic API:")
    try:
        from anthropic import Anthropic
        from shared.config import settings

        client = Anthropic(api_key=settings.anthropic_api_key)

        # Test with a minimal completion
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )

        print("  ✓ Connection successful")
        print(f"  ✓ Model: {message.model}")
        results.add_check("apis", "anthropic", True)

    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        results.add_check("apis", "anthropic", False, str(e))

    # Voyage AI API
    print("\n🚢 Voyage AI API:")
    try:
        import voyageai
        from shared.config import settings

        client = voyageai.Client(api_key=settings.voyage_api_key)

        # Test with a minimal embedding
        result = client.embed(["test"], model="voyage-3", input_type="document")

        print("  ✓ Connection successful")
        print(f"  ✓ Model: voyage-3")
        print(f"  ✓ Dimensions: {len(result.embeddings[0])}")
        results.add_check("apis", "voyage", True)

    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        results.add_check("apis", "voyage", False, str(e))

    # OpenAI API
    print("\n🎤 OpenAI API (Whisper):")
    try:
        from openai import OpenAI
        from shared.config import settings

        client = OpenAI(api_key=settings.openai_api_key)

        # Test with models list
        models = client.models.list()

        print("  ✓ Connection successful")
        print(f"  ✓ API accessible")
        results.add_check("apis", "openai", True)

    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        results.add_check("apis", "openai", False, str(e))

    # Tavily API (optional)
    print("\n🔍 Tavily API (optional):")
    try:
        from shared.config import settings

        if settings.tavily_api_key and settings.tavily_api_key.strip():
            # Note: We don't test Tavily directly as it requires MCP server
            print(f"  ✓ API key configured")
            print(f"  ℹ️  MCP server test requires running application")
            results.add_check("apis", "tavily", True)
        else:
            print("  - API key not configured (optional)")
            results.add_check("apis", "tavily_optional", True)

    except Exception as e:
        print(f"  ⚠️  Could not check: {e}")
        results.add_warning(f"Tavily check failed: {e}")

# =============================================================================
# BASIC OPERATIONS CHECK
# =============================================================================

def verify_operations(db_instance, results: VerificationResults, verbose: bool = False):
    """Verify basic CRUD operations work."""

    if not db_instance:
        print("\n⚠️  Skipping operations checks (no database connection)")
        return

    print("\n" + "="*70)
    print("CHECKING BASIC OPERATIONS")
    print("="*70)

    test_collection = db_instance["_setup_test"]

    # Insert
    print("\n📝 Testing INSERT:")
    try:
        test_doc = {
            "test_type": "verification",
            "timestamp": datetime.now(),
            "data": "test data"
        }
        result = test_collection.insert_one(test_doc)
        print(f"  ✓ Inserted document: {result.inserted_id}")
        results.add_check("operations", "insert", True)
    except Exception as e:
        print(f"  ✗ Insert failed: {e}")
        results.add_check("operations", "insert", False, str(e))
        return

    # Query
    print("\n🔍 Testing QUERY:")
    try:
        found_doc = test_collection.find_one({"_id": result.inserted_id})
        if found_doc:
            print(f"  ✓ Found document")
            results.add_check("operations", "query", True)
        else:
            print(f"  ✗ Document not found")
            results.add_check("operations", "query", False, "Document not found")
    except Exception as e:
        print(f"  ✗ Query failed: {e}")
        results.add_check("operations", "query", False, str(e))

    # Update
    print("\n✏️  Testing UPDATE:")
    try:
        update_result = test_collection.update_one(
            {"_id": result.inserted_id},
            {"$set": {"updated": True}}
        )
        if update_result.modified_count == 1:
            print(f"  ✓ Updated document")
            results.add_check("operations", "update", True)
        else:
            print(f"  ✗ Update failed (no documents modified)")
            results.add_check("operations", "update", False, "No documents modified")
    except Exception as e:
        print(f"  ✗ Update failed: {e}")
        results.add_check("operations", "update", False, str(e))

    # Delete
    print("\n🗑️  Testing DELETE:")
    try:
        delete_result = test_collection.delete_one({"_id": result.inserted_id})
        if delete_result.deleted_count == 1:
            print(f"  ✓ Deleted document")
            results.add_check("operations", "delete", True)
        else:
            print(f"  ✗ Delete failed (no documents deleted)")
            results.add_check("operations", "delete", False, "No documents deleted")
    except Exception as e:
        print(f"  ✗ Delete failed: {e}")
        results.add_check("operations", "delete", False, str(e))

    # Cleanup
    try:
        test_collection.drop()
        if verbose:
            print(f"\n  ✓ Cleaned up test collection")
    except Exception:
        pass

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Verify Flow Companion setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick check (environment + MongoDB only)"
    )

    parser.add_argument(
        "--skip-api",
        action="store_true",
        help="Skip API connectivity tests"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    results = VerificationResults()

    print("="*70)
    print("FLOW COMPANION - SETUP VERIFICATION")
    print("="*70)

    # Environment checks
    verify_environment(results, verbose=args.verbose)

    # MongoDB checks
    db = verify_mongodb(results, verbose=args.verbose)

    if args.quick:
        print("\n💡 Quick check complete. Run without --quick for full verification.")
        return 0 if results.print_summary() else 1

    # Collection checks
    verify_collections(db, results, verbose=args.verbose)

    # Index checks
    verify_indexes(db, results, verbose=args.verbose)

    # API checks
    if not args.skip_api:
        verify_apis(results, verbose=args.verbose)

    # Operations checks
    verify_operations(db, results, verbose=args.verbose)

    # Print summary
    success = results.print_summary()

    # Next steps
    if not success:
        print("\n📋 Troubleshooting:")
        print("  1. Check environment variables in .env file")
        print("  2. Verify MongoDB URI and database name")
        print("  3. Create missing collections: python scripts/init_db.py")
        print("  4. Create vector search indexes in Atlas UI")
        print("  5. Verify API keys are valid and have proper permissions")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
