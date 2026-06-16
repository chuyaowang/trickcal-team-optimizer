"""Pure (Streamlit-free) logic for the web pet selector.

Kept separate from web_gui.py so it can be unit-tested without importing
Streamlit (which runs page setup at import time). web_gui.py imports these
helpers for rendering and for its on_change callbacks.
"""
import base64
import functools
import os
from typing import Dict, List, Optional, Tuple

MAX_COPIES = 20
_COPY_SEP = "\x00"


@functools.lru_cache(maxsize=None)
def pet_icon_uri(thumb_path: Optional[str]) -> Optional[str]:
    """Base64 ``data:`` URI for a thumbnail, or None if missing/unset.

    Cached: pills call this per option on every rerun, and thumbnails are
    static for the life of the process.
    """
    if not thumb_path or not os.path.exists(thumb_path):
        return None
    with open(thumb_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/webp;base64,{data}"


def pet_label(pet: dict, with_name: bool) -> str:
    """Markdown label for a pet pill: thumbnail image, optionally + the name.

    Pure (no Streamlit) so it can be unit-tested. Falls back to the name when
    the pet has no thumbnail.
    """
    uri = pet_icon_uri(pet.get("thumb"))
    title = pet["name"].replace('"', "")
    img = f'![]({uri} "{title}")' if uri else ""
    if with_name:
        return f"{img} {pet['name']}".strip()
    return img if img else pet["name"]


def add_owned(owned: List[str], name: str) -> List[str]:
    """Owned list with ``name`` appended if absent (deduped, order kept)."""
    return list(owned) if name in owned else list(owned) + [name]


def remove_owned(owned: List[str], name: str) -> List[str]:
    """Owned list without ``name`` (unchanged if absent)."""
    return [n for n in owned if n != name]


def inc_borrow(counts: Dict[str, int], name: str,
               max_copies: int = MAX_COPIES) -> Dict[str, int]:
    """New counts with ``name`` incremented, capped at ``max_copies``."""
    out = dict(counts)
    out[name] = min(out.get(name, 0) + 1, max_copies)
    return out


def dec_borrow(counts: Dict[str, int], name: str) -> Dict[str, int]:
    """New counts with ``name`` decremented; the key is dropped at 0."""
    out = dict(counts)
    if name in out:
        if out[name] <= 1:
            del out[name]
        else:
            out[name] -= 1
    return out


def expand_borrow(counts: Dict[str, int]) -> List[str]:
    """One option value per copy: ``"<name>\\x00<i>"`` for each copy i."""
    values: List[str] = []
    for name, n in counts.items():
        values.extend(f"{name}{_COPY_SEP}{i}" for i in range(n))
    return values


def copy_value_name(value: str) -> str:
    """Parse the pet name back out of an expanded copy value."""
    return value.split(_COPY_SEP, 1)[0]


def state_to_config(owned: List[str], borrow_counts: Dict[str, int],
                    server: str, max_job_number: int, lang: str) -> dict:
    """Build the config dict from selector state (drops zero borrow counts)."""
    return {
        "server": server,
        "max_job_number": max_job_number,
        "owned_pets": list(owned),
        "aux_pets_counts": {k: v for k, v in borrow_counts.items() if v > 0},
        "ui_language": lang,
    }


def config_to_state(config: dict) -> Tuple[List[str], Dict[str, int]]:
    """Return ``(owned_set, borrow_counts)`` from a config dict (safe defaults)."""
    owned = list(config.get("owned_pets", []))
    counts = {k: int(v) for k, v in config.get("aux_pets_counts", {}).items()
              if int(v) > 0}
    return owned, counts
