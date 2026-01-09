#!/usr/bin/env python3
"""
All-in-One Setup Script for Flow Companion.

This is the single script a new developer should run to set up the entire
project from scratch. It orchestrates all setup steps in the correct order.

What it does:
    1. Checks Python version and dependencies
    2. Creates .env file (if missing) and validates environment
    3. Initializes MongoDB (collections + indexes)
    4. Verifies setup (health checks)
    5. Optionally seeds demo data
    6. Displays next steps

Usage:
    # Interactive setup (recommended for first-time)
    python scripts/setup.py

    # Non-interactive setup (use existing .env)
    python scripts/setup.py --non-interactive

    # Skip demo data seeding
    python scripts/setup.py --no-demo-data

    # Skip verification
    python scripts/setup.py --no-verify

    # Full reset (dangerous - drops all data!)
    python scripts/setup.py --reset
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from typing import Optional, Tuple

# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"

MIN_PYTHON_VERSION = (3, 9)

REQUIRED_ENV_VARS = {
    "ANTHROPIC_API_KEY": {
        "description": "Claude API key from Anthropic",
        "url": "https://console.anthropic.com/",
        "format": "sk-ant-xxxxx",
        "required": True
    },
    "VOYAGE_API_KEY": {
        "description": "Voyage AI embeddings API key",
        "url": "https://dash.voyageai.com/",
        "format": "pa-xxxxx",
        "required": True
    },
    "OPENAI_API_KEY": {
        "description": "OpenAI API key (for Whisper voice transcription)",
        "url": "https://platform.openai.com/api-keys",
        "format": "sk-xxxxx",
        "required": True
    },
    "MONGODB_URI": {
        "description": "MongoDB Atlas connection string",
        "url": "https://cloud.mongodb.com/",
        "format": "mongodb+srv://user:pass@cluster.mongodb.net/",
        "required": True
    },
    "MONGODB_DATABASE": {
        "description": "MongoDB database name",
        "url": None,
        "format": "flow_companion",
        "required": True
    },
    "TAVILY_API_KEY": {
        "description": "Tavily API key (optional - for web search via MCP)",
        "url": "https://tavily.com/",
        "format": "tvly-xxxxx",
        "required": False
    }
}

# =============================================================================
# UTILITIES
# =============================================================================

def print_banner(text: str):
    """Print a formatted banner."""
    print("\n" + "="*70)
    print(text)
    print("="*70)

def print_step(number: int, total: int, text: str):
    """Print a step header."""
    print(f"\n{'='*70}")
    print(f"STEP {number}/{total}: {text}")
    print(f"{'='*70}")

def run_command(cmd: list, description: str, check: bool = True) -> Tuple[bool, str]:
    """
    Run a shell command and return success status and output.

    Args:
        cmd: Command as list of strings
        description: Human-readable description
        check: If True, raise error on failure

    Returns:
        Tuple of (success, output)
    """
    print(f"\n🔧 {description}...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check,
            cwd=PROJECT_ROOT
        )

        if result.returncode == 0:
            print(f"✓ {description} completed")
            return True, result.stdout
        else:
            print(f"✗ {description} failed")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}")
            return False, result.stderr

    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr[:200]}")
        return False, e.stderr
    except Exception as e:
        print(f"✗ {description} failed: {e}")
        return False, str(e)

def check_python_version() -> bool:
    """Check if Python version meets minimum requirements."""
    current = sys.version_info[:2]
    if current >= MIN_PYTHON_VERSION:
        print(f"✓ Python {current[0]}.{current[1]} (minimum: {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]})")
        return True
    else:
        print(f"✗ Python {current[0]}.{current[1]} is too old (minimum: {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]})")
        return False

def check_dependencies() -> bool:
    """Check if required Python packages are installed."""
    print("\n📦 Checking dependencies...")

    # Map package names to their import names (when different)
    package_import_names = {
        "python-dotenv": "dotenv"
    }

    required_packages = [
        "anthropic",
        "voyageai",
        "openai",
        "pymongo",
        "streamlit",
        "pydantic",
        "python-dotenv"
    ]

    missing = []
    for package in required_packages:
        try:
            # Use mapped import name if exists, otherwise convert dashes to underscores
            import_name = package_import_names.get(package, package.replace("-", "_"))
            __import__(import_name)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"✗ Missing packages: {', '.join(missing)}")
        print("\n💡 Install with: pip install -r requirements.txt")
        return False
    else:
        print(f"✓ All required packages installed")
        return True

# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================

def create_env_file(interactive: bool = True) -> bool:
    """Create .env file from user input or template."""

    if ENV_FILE.exists():
        print(f"\n✓ .env file already exists: {ENV_FILE}")
        return True

    print_step(2, 6, "ENVIRONMENT CONFIGURATION")

    if not interactive:
        print("\n✗ .env file not found and non-interactive mode specified")
        print(f"  Create {ENV_FILE} manually or run without --non-interactive")
        return False

    print("\n📝 .env file not found. Let's create it!")
    print("\nYou'll need to provide API keys and MongoDB credentials.")
    print("Press Enter to skip optional values.\n")

    env_contents = []

    # Collect required and optional variables
    for var_name, var_info in REQUIRED_ENV_VARS.items():
        print(f"\n{var_name}:")
        print(f"  Description: {var_info['description']}")
        if var_info['url']:
            print(f"  Get key from: {var_info['url']}")
        print(f"  Format: {var_info['format']}")

        if var_info['required']:
            while True:
                value = input(f"  Enter value: ").strip()
                if value:
                    env_contents.append(f"{var_name}={value}")
                    break
                else:
                    print("  ✗ This value is required. Please enter a value.")
        else:
            value = input(f"  Enter value (optional): ").strip()
            if value:
                env_contents.append(f"{var_name}={value}")
            else:
                env_contents.append(f"# {var_name}=  # Optional")

    # Add additional optional vars
    env_contents.append("\n# Optional settings")
    env_contents.append("MONGODB_MCP_ENABLED=false")
    env_contents.append("MCP_MODE_ENABLED=false")
    env_contents.append("LOG_LEVEL=INFO")
    env_contents.append("DEBUG=false")

    # Write to file
    try:
        ENV_FILE.write_text("\n".join(env_contents) + "\n")
        print(f"\n✓ Created .env file: {ENV_FILE}")
        return True
    except Exception as e:
        print(f"\n✗ Failed to create .env file: {e}")
        return False

def validate_environment() -> bool:
    """Validate environment variables are set correctly."""

    print("\n🔍 Validating environment variables...")

    # Load environment from .env
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)

    missing = []
    warnings = []

    for var_name, var_info in REQUIRED_ENV_VARS.items():
        value = os.getenv(var_name)

        if var_info['required']:
            if not value:
                missing.append(var_name)
                print(f"  ✗ {var_name}: NOT SET (required)")
            else:
                print(f"  ✓ {var_name}: set")

                # Format validation
                expected_format = var_info['format']
                if expected_format.startswith("sk-") and not value.startswith("sk-"):
                    warnings.append(f"{var_name} doesn't start with 'sk-' (expected format: {expected_format})")
                elif expected_format.startswith("pa-") and not value.startswith("pa-"):
                    warnings.append(f"{var_name} doesn't start with 'pa-' (expected format: {expected_format})")
                elif expected_format.startswith("mongodb") and not value.startswith("mongodb"):
                    warnings.append(f"{var_name} doesn't start with 'mongodb' (expected format: {expected_format})")
        else:
            if value:
                print(f"  ✓ {var_name}: set (optional)")
            else:
                print(f"  - {var_name}: not set (optional)")

    if missing:
        print(f"\n✗ Missing required variables: {', '.join(missing)}")
        print(f"  Edit {ENV_FILE} and add the missing values")
        return False

    if warnings:
        print(f"\n⚠️  Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    print(f"\n✓ Environment validation passed")
    return True

# =============================================================================
# SETUP ORCHESTRATION
# =============================================================================

def run_init_db(force: bool = False) -> bool:
    """Run database initialization script."""

    print_step(3, 6, "DATABASE INITIALIZATION")

    cmd = [sys.executable, "scripts/init_db.py"]
    if force:
        cmd.append("--force")
        print("\n⚠️  Force mode: Will drop and recreate collections!")

    success, _ = run_command(cmd, "Initialize MongoDB collections and indexes")
    return success

def run_verification(quick: bool = False) -> bool:
    """Run setup verification script."""

    print_step(4, 6, "VERIFICATION")

    cmd = [sys.executable, "scripts/verify_setup.py"]
    if quick:
        cmd.append("--quick")

    success, output = run_command(cmd, "Verify setup", check=False)

    # verification script returns detailed output, always show it
    if output:
        print(output)

    return success

def run_demo_seeding() -> bool:
    """Run demo data seeding script."""

    print_step(5, 6, "DEMO DATA (Optional)")

    response = input("\nSeed demo data? (yes/no) [yes]: ").strip().lower()

    if response in ["", "yes", "y"]:
        cmd = [sys.executable, "scripts/seed_demo_data.py"]
        success, _ = run_command(cmd, "Seed demo data")
        return success
    else:
        print("\n⏭️  Skipping demo data seeding")
        return True

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="All-in-one setup for Flow Companion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Non-interactive mode (requires existing .env file)"
    )

    parser.add_argument(
        "--no-demo-data",
        action="store_true",
        help="Skip demo data seeding"
    )

    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip verification step"
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (DANGEROUS: drops all collections)"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick verification (environment + MongoDB only)"
    )

    args = parser.parse_args()

    # Banner
    print_banner("FLOW COMPANION - FIRST-TIME SETUP")
    print("\nThis script will set up your local development environment.")
    print("It will:")
    print("  1. Check Python version and dependencies")
    print("  2. Create/validate .env file")
    print("  3. Initialize MongoDB database")
    print("  4. Verify everything works")
    print("  5. Optionally seed demo data")

    if args.reset:
        print("\n⚠️  WARNING: --reset will DROP ALL DATA in your database!")
        response = input("\nContinue? (type 'yes' to confirm): ").strip().lower()
        if response != "yes":
            print("\n❌ Aborted")
            return 1

    # Step 1: Pre-flight checks
    print_step(1, 6, "PRE-FLIGHT CHECKS")

    if not check_python_version():
        return 1

    if not check_dependencies():
        return 1

    # Step 2: Environment setup
    if not create_env_file(interactive=not args.non_interactive):
        return 1

    if not validate_environment():
        return 1

    # Step 3: Database initialization
    if not run_init_db(force=args.reset):
        print("\n✗ Database initialization failed")
        print("  See errors above for details")
        return 1

    # Step 4: Verification
    if not args.no_verify:
        verify_success = run_verification(quick=args.quick)
        if not verify_success:
            print("\n⚠️  Verification found issues")
            print("  Review errors above and fix before proceeding")

            response = input("\nContinue anyway? (yes/no) [no]: ").strip().lower()
            if response not in ["yes", "y"]:
                return 1
    else:
        print_step(4, 6, "VERIFICATION (Skipped)")

    # Step 5: Demo data
    if not args.no_demo_data and not args.non_interactive:
        run_demo_seeding()
    else:
        print_step(5, 6, "DEMO DATA (Skipped)")

    # Step 6: Final instructions
    print_step(6, 6, "SETUP COMPLETE!")

    print("\n✅ Flow Companion is ready to use!\n")

    print("📋 Next Steps:")
    print("\n1. Start the application:")
    print("   streamlit run streamlit_app.py")
    print("\n2. Open your browser to:")
    print("   http://localhost:8501")
    print("\n3. (Optional) Create vector search indexes:")
    print("   python scripts/init_db.py --vector-instructions")
    print("   Then create them manually in MongoDB Atlas UI")

    print("\n📚 Useful Commands:")
    print("   python scripts/verify_setup.py          # Verify setup")
    print("   python scripts/seed_demo_data.py        # Seed demo data")
    print("   python scripts/reset_demo.py --force    # Reset demo data")
    print("   streamlit run streamlit_app.py          # Start app")
    print("   streamlit run evals_app.py              # Start evals dashboard")

    print("\n🔧 Development:")
    print("   pytest tests/                           # Run tests")
    print("   python scripts/verify_setup.py --verbose  # Detailed verification")

    print("\n💡 Tips:")
    print("   - Demo user ID: demo-user")
    print("   - Check docs/testing/ for test guides")
    print("   - See README.md for architecture overview")

    print("\n🎉 Happy coding!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
