from scripts.migrate_pet_data import merge_rows, PetRow


def test_merge_links_same_pet_across_languages_by_signature():
    # Unambiguous signature in two languages -> one merged row with both names
    rows = [
        PetRow(lang="en", name="Sato", rarity="NORMAL",
               t1="KIND", r1="C", t2="DULL", r2="C"),
        PetRow(lang="zh_hans", name="莎兔", rarity="NORMAL",
               t1="KIND", r1="C", t2="DULL", r2="C"),
    ]
    records, expanded = merge_rows(rows)
    assert expanded == []
    assert len(records) == 1
    m = records[0]
    assert m["rarity_key"] == "NORMAL"
    assert m["trait_1"] == "KIND" and m["rank_1"] == "C"
    assert m["name_en"] == "Sato"
    assert m["name_zh_hans"] == "莎兔"
    assert m["name_zh_hant"] == "" and m["name_ko"] == ""


def test_distinct_signatures_stay_separate():
    rows = [
        PetRow(lang="en", name="Sato", rarity="NORMAL",
               t1="KIND", r1="C", t2="DULL", r2="C"),
        PetRow(lang="en", name="Petit L1ly", rarity="UNIQUE",
               t1="BOLD", r1="A", t2="KEEN", r2="C"),
    ]
    records, expanded = merge_rows(rows)
    assert expanded == []
    assert len(records) == 2


def test_ambiguous_signature_emits_cartesian_candidate_rows():
    # Two pets share a signature in two languages -> 2x2 = 4 candidate rows
    rows = [
        PetRow(lang="en", name="A", rarity="UNIQUE",
               t1="BOLD", r1="A", t2="KEEN", r2="C"),
        PetRow(lang="en", name="B", rarity="UNIQUE",
               t1="BOLD", r1="A", t2="KEEN", r2="C"),
        PetRow(lang="zh_hans", name="甲", rarity="UNIQUE",
               t1="BOLD", r1="A", t2="KEEN", r2="C"),
        PetRow(lang="zh_hans", name="乙", rarity="UNIQUE",
               t1="BOLD", r1="A", t2="KEEN", r2="C"),
    ]
    records, expanded = merge_rows(rows)
    assert len(expanded) == 1
    assert expanded[0]["counts"] == {"en": 2, "zh_hans": 2}
    assert len(records) == 4
    pairs = {(r["name_en"], r["name_zh_hans"]) for r in records}
    assert pairs == {("A", "甲"), ("A", "乙"), ("B", "甲"), ("B", "乙")}