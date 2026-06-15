from scripts.migrate_pet_data import merge_rows, PetRow


def test_merge_links_same_pet_across_languages_by_signature():
    # Same signature in two languages -> one merged row with both names
    rows = [
        PetRow(lang="en", name="Sato", rarity="NORMAL",
               t1="KIND", r1="C", t2="DULL", r2="C"),
        PetRow(lang="zh_hans", name="莎兔", rarity="NORMAL",
               t1="KIND", r1="C", t2="DULL", r2="C"),
    ]
    merged, collisions = merge_rows(rows)
    assert collisions == []
    assert len(merged) == 1
    m = merged[0]
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
    merged, collisions = merge_rows(rows)
    assert collisions == []
    assert len(merged) == 2


def test_same_signature_twice_in_one_language_is_a_collision():
    rows = [
        PetRow(lang="en", name="A", rarity="NORMAL",
               t1="KIND", r1="C", t2="DULL", r2="C"),
        PetRow(lang="en", name="B", rarity="NORMAL",
               t1="KIND", r1="C", t2="DULL", r2="C"),
    ]
    merged, collisions = merge_rows(rows)
    assert len(collisions) == 1
    assert collisions[0]["lang"] == "en"
    assert set(collisions[0]["names"]) == {"A", "B"}