import os
from src.ui import pet_selector as ps


def test_add_owned_dedupes_and_preserves_order():
    assert ps.add_owned([], "Inky") == ["Inky"]
    assert ps.add_owned(["Inky"], "Sato") == ["Inky", "Sato"]
    assert ps.add_owned(["Inky"], "Inky") == ["Inky"]  # no duplicate


def test_remove_owned():
    assert ps.remove_owned(["Inky", "Sato"], "Inky") == ["Sato"]
    assert ps.remove_owned(["Sato"], "Inky") == ["Sato"]  # absent -> unchanged


def test_inc_borrow_caps_at_max():
    assert ps.inc_borrow({}, "Inky") == {"Inky": 1}
    assert ps.inc_borrow({"Inky": 1}, "Inky") == {"Inky": 2}
    assert ps.inc_borrow({"Inky": 20}, "Inky", max_copies=20) == {"Inky": 20}


def test_dec_borrow_removes_at_zero():
    assert ps.dec_borrow({"Inky": 2}, "Inky") == {"Inky": 1}
    assert ps.dec_borrow({"Inky": 1}, "Inky") == {}
    assert ps.dec_borrow({}, "Inky") == {}


def test_expand_borrow_and_parse_roundtrip():
    counts = {"Inky": 3, "Sato": 1}
    values = ps.expand_borrow(counts)
    assert len(values) == 4
    assert sum(1 for v in values if ps.copy_value_name(v) == "Inky") == 3
    # names with odd characters survive the round-trip
    assert ps.copy_value_name(ps.expand_borrow({"A B#1": 1})[0]) == "A B#1"


def test_state_config_roundtrip_drops_zero_counts():
    cfg = ps.state_to_config(["Inky"], {"Sato": 2, "Z": 0}, "cn", 5, "en")
    assert cfg["owned_pets"] == ["Inky"]
    assert cfg["aux_pets_counts"] == {"Sato": 2}
    assert cfg["server"] == "cn" and cfg["max_job_number"] == 5 and cfg["ui_language"] == "en"
    owned, counts = ps.config_to_state(cfg)
    assert owned == ["Inky"] and counts == {"Sato": 2}


def test_config_to_state_defaults_when_keys_missing():
    assert ps.config_to_state({}) == ([], {})


def test_available_thumb_ids(tmp_path):
    d = tmp_path / "pet_thumbs"
    d.mkdir()
    (d / "353924.webp").write_bytes(b"x")
    (d / "10000.webp").write_bytes(b"x")
    (d / "notes.txt").write_bytes(b"x")   # non-webp ignored
    assert ps.available_thumb_ids(str(d)) == frozenset({"353924", "10000"})
    # missing dir -> empty set (no crash)
    assert ps.available_thumb_ids(str(tmp_path / "nope")) == frozenset()


def test_pet_label():
    available = frozenset({"353924"})

    # Has a thumbnail -> served-URL markdown image (quote stripped from title)
    pet = {"id": "353924", "name": 'Sa"to'}
    assert ps.pet_label(pet, available, with_name=False) == (
        '![](app/static/pet_thumbs/353924.webp "Sato")'
    )
    assert ps.pet_label(pet, available, with_name=True) == (
        '![](app/static/pet_thumbs/353924.webp "Sato") Sa"to'
    )

    # No thumbnail for this id, or no id -> name only
    assert ps.pet_label({"id": "999", "name": "Inky"}, available, with_name=False) == "Inky"
    assert ps.pet_label({"id": None, "name": "Inky"}, available, with_name=True) == "Inky"
