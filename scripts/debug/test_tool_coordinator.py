#!/usr/bin/env python3
"""Test the new tool-based coordinator."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.coordinator import coordinator

def test_query(message, input_type="text"):
    """Test a query with the coordinator."""
    print("=" * 80)
    print(f"[{input_type.upper()}] {message}")
    print("=" * 80)

    try:
        response = coordinator.process(message, [], input_type=input_type)
        print("\nRESPONSE:")
        print("-" * 80)
        print(response)
        print("-" * 80)
        print()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        print()

if __name__ == "__main__":
    # Test cases: voice and text should work identically
    test_cases = [
        ("I finished the debugging doc", "voice"),
        ("I finished the debugging doc", "text"),
        ("What are my tasks?", "text"),
        ("Show me the checkpointer task", "text"),
    ]

    for message, input_type in test_cases:
        test_query(message, input_type)
        print("\n" * 2)
