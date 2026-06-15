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


def test_pet_icon_uri(tmp_path):
    assert ps.pet_icon_uri(None) is None
    assert ps.pet_icon_uri(str(tmp_path / "missing.png")) is None
    p = tmp_path / "t.png"
    p.write_bytes(b"RIFF0000WEBP")
    uri = ps.pet_icon_uri(str(p))
    assert uri.startswith("data:image/webp;base64,")
