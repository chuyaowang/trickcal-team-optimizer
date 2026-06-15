import csv
import os

from src.data_loader import vocab_loader, csv_loader


def _write_master(tmp_path):
    data_dir = tmp_path / "data"
    (data_dir / "i18n").mkdir(parents=True)
    with open(data_dir / "i18n" / "traits.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "en", "zh_hans", "zh_hant", "ko"])
        w.writerow(["KIND", "Kind", "体贴", "體貼", ""])
        w.writerow(["DULL", "Dull", "迟钝", "遲鈍", ""])
    with open(data_dir / "i18n" / "rarity.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "en", "zh_hans", "zh_hant", "ko"])
        w.writerow(["NORMAL", "Normal", "普通宠物", "普通寵物", ""])
    with open(data_dir / "pets.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "rarity_key", "trait_1", "rank_1", "trait_2", "rank_2",
                    "name_en", "name_zh_hans", "name_zh_hant", "name_ko"])
        # On en + cn, not on kr (blank name_ko)
        w.writerow(["148590", "NORMAL", "KIND", "C", "DULL", "C",
                    "Sato", "莎兔", "蘋果兔", ""])
    return str(data_dir)


def test_load_pets_filters_by_server_language_and_keys(tmp_path, monkeypatch):
    data_dir = _write_master(tmp_path)
    monkeypatch.setattr(vocab_loader, "_I18N_DIR", os.path.join(data_dir, "i18n"))
    vocab_loader._load_table.cache_clear()
    vocab_loader._reverse_table.cache_clear()

    pets_en = csv_loader.load_pets(server="gl-en", data_dir=data_dir)
    assert len(pets_en) == 1
    p = pets_en[0]
    assert p["name"] == "Sato"
    assert p["id"] == "148590"
    assert p["rarity_score"] == 2
    assert p["rarity"] == "Normal"  # localized display string (backward compat)
    assert p["skill_score"] == {"KIND": 7, "DULL": 7}
    assert p["is_borrowed"] is False

    # kr has no name -> pet absent
    pets_kr = csv_loader.load_pets(server="kr", data_dir=data_dir)
    assert pets_kr == []


def test_load_pets_sets_thumb_when_present(tmp_path, monkeypatch):
    data_dir = _write_master(tmp_path)
    monkeypatch.setattr(vocab_loader, "_I18N_DIR", os.path.join(data_dir, "i18n"))
    vocab_loader._load_table.cache_clear()
    vocab_loader._reverse_table.cache_clear()

    # No thumbnail file yet -> thumb is None
    pets = csv_loader.load_pets(server="gl-en", data_dir=data_dir)
    assert pets[0]["thumb"] is None

    # Create the thumbnail -> thumb resolves to it
    thumb_dir = os.path.join(data_dir, "pet_images", "thumbnails")
    os.makedirs(thumb_dir, exist_ok=True)
    thumb_path = os.path.join(thumb_dir, "148590.png")
    with open(thumb_path, "wb") as f:
        f.write(b"RIFF0000WEBP")  # any bytes; load_pets only checks existence
    pets = csv_loader.load_pets(server="gl-en", data_dir=data_dir)
    assert pets[0]["thumb"] == thumb_path