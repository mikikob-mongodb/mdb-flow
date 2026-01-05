"""MongoDB storage for eval comparison runs."""

from datetime import datetime
from typing import Optional, List
from bson import ObjectId

from evals.result import ComparisonRun


def get_evals_collection():
    """Get the eval_comparison_runs collection."""
    from shared.db import get_db
    db = get_db()
    return db.eval_comparison_runs


def save_comparison_run(run: ComparisonRun) -> str:
    """
    Save a comparison run to MongoDB.

    Returns:
        The inserted document ID
    """
    collection = get_evals_collection()

    doc = run.to_dict()
    doc["_id"] = ObjectId()
    doc["saved_at"] = datetime.utcnow()

    result = collection.insert_one(doc)
    return str(result.inserted_id)


def load_comparison_run(run_id: str) -> Optional[dict]:
    """Load a comparison run by run_id."""
    collection = get_evals_collection()
    return collection.find_one({"run_id": run_id})


def load_latest_run() -> Optional[dict]:
    """Load the most recent comparison run."""
    collection = get_evals_collection()
    return collection.find_one(sort=[("timestamp", -1)])


def list_comparison_runs(limit: int = 20) -> List[dict]:
    """List recent comparison runs (summary only)."""
    collection = get_evals_collection()

    runs = collection.find(
        {},
        {
            "run_id": 1,
            "timestamp": 1,
            "configs_compared": 1,
            "summary_by_config": 1
        }
    ).sort("timestamp", -1).limit(limit)

    return list(runs)


def delete_comparison_run(run_id: str) -> bool:
    """Delete a comparison run."""
    collection = get_evals_collection()
    result = collection.delete_one({"run_id": run_id})
    return result.deleted_count > 0
