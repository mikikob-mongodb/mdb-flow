#!/usr/bin/env python3
"""Test hybrid search directly."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.retrieval import retrieval_agent

def test_hybrid_search(query):
    """Test hybrid search with a query."""
    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    results = retrieval_agent.hybrid_search_tasks(query, limit=5)

    if results:
        print(f"\nFound {len(results)} results:\n")
        for i, task in enumerate(results, 1):
            score = task.get('score', 0)
            status_icon = {"todo": "○", "in_progress": "◐", "done": "✓"}.get(task.get('status'), "○")
            print(f"{i}. [{score:.3f}] {status_icon} {task['title']}")
    else:
        print("\nNo results found")

    print()


if __name__ == "__main__":
    # Test the specific examples
    test_queries = [
        "the debugging doc",
        "checkpointer task",
        "voice agent app",
    ]

    for query in test_queries:
        test_hybrid_search(query)
        print("\n")
