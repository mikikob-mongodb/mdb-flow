#!/usr/bin/env bash
#
# Test runner for slash commands
# Runs the complete slash command test suite
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "  Slash Commands Test Suite"
echo "============================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
    echo "Attempting to activate venv..."
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}Error: venv not found. Please activate your virtual environment.${NC}"
        exit 1
    fi
fi

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${RED}Error: pytest not installed${NC}"
    echo "Install with: pip install pytest pytest-cov"
    exit 1
fi

# Parse command line arguments
VERBOSE=""
COVERAGE=""
SPECIFIC_TEST=""
MARKERS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -vv|--very-verbose)
            VERBOSE="-vv"
            shift
            ;;
        --cov|--coverage)
            COVERAGE="--cov=ui.slash_commands --cov-report=term-missing"
            shift
            ;;
        -k|--keyword)
            SPECIFIC_TEST="-k $2"
            shift 2
            ;;
        -m|--marker)
            MARKERS="-m $2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose          Verbose output"
            echo "  -vv, --very-verbose    Very verbose output"
            echo "  --cov, --coverage      Run with coverage report"
            echo "  -k, --keyword EXPR     Run tests matching keyword expression"
            echo "  -m, --marker MARKER    Run tests with specific marker"
            echo "  --help                 Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Run all tests"
            echo "  $0 -v                                 # Run with verbose output"
            echo "  $0 --cov                              # Run with coverage"
            echo "  $0 -k test_filter_by_status           # Run specific test"
            echo "  $0 -k TestTasksSearch                 # Run specific test class"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run the tests
echo "Running tests..."
echo ""

pytest tests/ui/test_slash_commands.py \
    $VERBOSE \
    $COVERAGE \
    $SPECIFIC_TEST \
    $MARKERS \
    --tb=short \
    --color=yes

TEST_RESULT=$?

echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

echo ""
echo "============================================"

exit $TEST_RESULT
