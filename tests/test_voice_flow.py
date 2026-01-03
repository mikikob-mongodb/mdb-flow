#!/usr/bin/env python3
"""Test script for voice input flow."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.coordinator import coordinator

def test_voice_input(transcript):
    """Test voice input processing."""
    print("=" * 80)
    print(f"TESTING VOICE INPUT: {transcript}")
    print("=" * 80)

    # Process the voice input
    response = coordinator.process(transcript, [], input_type="voice")

    print("\nAGENT RESPONSE:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    print()

    return response


if __name__ == "__main__":
    # Test various voice inputs
    test_cases = [
        "I finished the debugging doc",
        "I'm working on the authentication feature",
        "Add a note to the API integration: need to update the docs",
        "Show me the AgentOps project",
    ]

    for test in test_cases:
        test_voice_input(test)
        print("\n" * 2)
