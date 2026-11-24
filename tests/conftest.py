import pytest

from src.data_loader import vocab_loader


@pytest.fixture(autouse=True)
def _clear_vocab_cache():
    """Isolate the vocab_loader lru_cache between tests.

    Some tests monkeypatch vocab_loader._I18N_DIR to a temp directory; without
    clearing the cache, a table loaded from the temp dir would leak into later
    tests (and vice versa).
    """
    caches = (vocab_loader._load_table, vocab_loader._reverse_table,
              vocab_loader._load_locations)
    for c in caches:
        c.cache_clear()
    yield
    for c in caches:
        c.cache_clear()
