"""Shared test utilities and helpers."""

from typing import List, Dict, Any, Callable
import time
from datetime import datetime


def assert_all_have_field(items: List[Dict], field: str, message: str = None):
    """Assert all items in list have a specific field."""
    if message is None:
        message = f"All items should have '{field}' field"
    
    missing = [i for i, item in enumerate(items) if field not in item]
    assert len(missing) == 0, f"{message}. Missing in items at indices: {missing}"


def assert_all_match(items: List[Dict], condition: Callable[[Dict], bool], message: str = None):
    """Assert all items match a condition."""
    if message is None:
        message = "All items should match condition"
    
    failures = [(i, item) for i, item in enumerate(items) if not condition(item)]
    assert len(failures) == 0, f"{message}. Failed at indices: {[i for i, _ in failures]}"


def assert_sorted_by(items: List[Dict], key: str, reverse: bool = False, message: str = None):
    """Assert items are sorted by a specific key."""
    if message is None:
        order = "descending" if reverse else "ascending"
        message = f"Items should be sorted by '{key}' in {order} order"
    
    values = [item[key] for item in items if key in item]
    expected = sorted(values, reverse=reverse)
    assert values == expected, message


def measure_execution_time(func: Callable, *args, **kwargs) -> tuple:
    """
    Measure execution time of a function.
    
    Returns:
        tuple: (result, duration_ms)
    """
    start = time.time()
    result = func(*args, **kwargs)
    duration_ms = (time.time() - start) * 1000
    return result, duration_ms


def assert_execution_time_under(func: Callable, threshold_ms: int, *args, **kwargs):
    """Assert function executes within time threshold."""
    result, duration_ms = measure_execution_time(func, *args, **kwargs)
    assert duration_ms < threshold_ms, \
        f"Execution took {duration_ms:.1f}ms, expected < {threshold_ms}ms"
    return result


def strip_mongo_fields(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Strip MongoDB-specific fields from document."""
    cleaned = dict(doc)
    for field in ["_id", "created_at", "updated_at", "embedding"]:
        cleaned.pop(field, None)
    return cleaned


def assert_contains_text(text: str, *substrings: str, case_sensitive: bool = False):
    """Assert text contains all substrings."""
    if not case_sensitive:
        text = text.lower()
        substrings = [s.lower() for s in substrings]
    
    missing = [s for s in substrings if s not in text]
    assert len(missing) == 0, f"Text missing expected substrings: {missing}"


def assert_not_contains_text(text: str, *substrings: str, case_sensitive: bool = False):
    """Assert text does not contain any substrings."""
    if not case_sensitive:
        text = text.lower()
        substrings = [s.lower() for s in substrings]
    
    found = [s for s in substrings if s in text]
    assert len(found) == 0, f"Text contains unexpected substrings: {found}"


def assert_valid_objectid(value: Any):
    """Assert value is a valid MongoDB ObjectId."""
    from bson import ObjectId
    from bson.errors import InvalidId
    
    try:
        if isinstance(value, str):
            ObjectId(value)
        elif isinstance(value, ObjectId):
            pass  # Already valid
        else:
            raise InvalidId(f"Not a valid ObjectId: {type(value)}")
    except InvalidId as e:
        raise AssertionError(f"Invalid ObjectId: {e}")


def assert_recent_timestamp(timestamp: datetime, max_age_seconds: int = 60):
    """Assert timestamp is recent (within max_age_seconds of now)."""
    now = datetime.utcnow()
    age = (now - timestamp).total_seconds()
    assert age >= 0, f"Timestamp is in the future: {timestamp}"
    assert age <= max_age_seconds, \
        f"Timestamp is too old: {age:.1f}s > {max_age_seconds}s"


def create_test_embedding(seed: int = 0) -> List[float]:
    """Create a deterministic test embedding."""
    import random
    random.seed(seed)
    return [random.random() for _ in range(1024)]


def assert_embeddings_different(emb1: List[float], emb2: List[float]):
    """Assert two embeddings are different."""
    assert len(emb1) == len(emb2), "Embeddings must be same length"
    assert emb1 != emb2, "Embeddings should be different"


def assert_embeddings_similar(emb1: List[float], emb2: List[float], threshold: float = 0.9):
    """Assert two embeddings are similar (cosine similarity > threshold)."""
    import math
    
    # Calculate cosine similarity
    dot_product = sum(a * b for a, b in zip(emb1, emb2))
    magnitude1 = math.sqrt(sum(a * a for a in emb1))
    magnitude2 = math.sqrt(sum(b * b for b in emb2))
    
    similarity = dot_product / (magnitude1 * magnitude2) if magnitude1 and magnitude2 else 0
    
    assert similarity >= threshold, \
        f"Embeddings not similar enough: {similarity:.3f} < {threshold}"
