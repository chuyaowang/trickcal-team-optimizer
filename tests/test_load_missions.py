import csv

import pytest

from src.data_loader import vocab_loader, csv_loader


def _write(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(rows)


@pytest.fixture
def i18n(tmp_path, monkeypatch):
    d = tmp_path / "i18n"
    d.mkdir()
    _write(d / "traits.csv", [
        ["key", "en", "ja", "zh_hant", "ko"],
        ["KIND", "Kind", "配慮", "體貼", ""],
        ["KEEN", "Keen", "鋭さ", "敏銳", ""],
    ])
    _write(d / "locations.csv", [
        ["key", "region", "location_en", "task_en", "location_zh_hant",
         "task_zh_hant", "location_ko", "task_ko"],
        ["LAKE", "5", "Lake", "Playing in Water", "湖", "玩水", "", ""],
    ])
    monkeypatch.setattr(vocab_loader, "_I18N_DIR", str(d))
    return d


def _missions(tmp_path, *rows):
    path = tmp_path / "missions_260101.csv"
    _write(path, [["location", "trait_1", "trait_2"], *rows])
    return str(path)


def test_load_missions_translates_location_and_traits(tmp_path, i18n):
    path = _missions(tmp_path, ["LAKE", "KEEN", "KIND"])
    assert csv_loader.load_missions(path, lang="zh_hant") == [
        {"task": "湖 - 玩水", "bonus_skills": ["KEEN", "KIND"]}
    ]


def test_blank_trait_2_is_omitted(tmp_path, i18n):
    path = _missions(tmp_path, ["LAKE", "KEEN", ""])
    assert csv_loader.load_missions(path, lang="en")[0]["bonus_skills"] == ["KEEN"]


def test_missing_translation_falls_back_to_english(tmp_path, i18n):
    path = _missions(tmp_path, ["LAKE", "KEEN", ""])
    assert csv_loader.load_missions(path, lang="ko")[0]["task"] == "Lake - Playing in Water"


def test_whitespace_is_stripped(tmp_path, i18n):
    path = _missions(tmp_path, [" LAKE ", " KEEN ", ""])
    tasks = csv_loader.load_missions(path, lang="en")
    assert tasks == [{"task": "Lake - Playing in Water", "bonus_skills": ["KEEN"]}]


def test_blank_rows_are_skipped(tmp_path, i18n):
    path = _missions(tmp_path, ["LAKE", "KEEN", ""], ["", "", ""])
    assert csv_loader.load_missions(path, lang="en") == [
        {"task": "Lake - Playing in Water", "bonus_skills": ["KEEN"]}
    ]


def test_unknown_location_raises(tmp_path, i18n):
    path = _missions(tmp_path, ["NOPE", "KEEN", ""])
    with pytest.raises(ValueError, match="NOPE"):
        csv_loader.load_missions(path, lang="en")


def test_unknown_trait_raises(tmp_path, i18n):
    path = _missions(tmp_path, ["LAKE", "NOPE", ""])
    with pytest.raises(ValueError, match="NOPE"):
        csv_loader.load_missions(path, lang="en")


def test_location_regions(i18n):
    assert vocab_loader.location_regions() == {"LAKE": 5}


def test_get_available_mission_files_sorted(tmp_path):
    m = tmp_path / "missions"
    m.mkdir()
    for d in ("261119", "260326"):
        _write(m / f"missions_{d}.csv", [["location", "trait_1", "trait_2"]])
    files = csv_loader.get_available_mission_files(data_dir=str(tmp_path))
    assert [f.rsplit("/", 1)[-1].rsplit("\\", 1)[-1] for f in files] == [
        "missions_260326.csv", "missions_261119.csv"]
