from src.data_loader import vocab_loader


def test_trait_name_translates_key_to_language():
    assert vocab_loader.trait_name("KIND", "zh_hans") == "体贴"
    assert vocab_loader.trait_name("KIND", "en") == "Kind"


def test_trait_key_from_localized_is_reverse_of_trait_name():
    assert vocab_loader.trait_key_from_localized("体贴", "zh_hans") == "KIND"
    assert vocab_loader.trait_key_from_localized("Kind", "en") == "KIND"


def test_trait_key_from_localized_returns_none_for_unknown():
    assert vocab_loader.trait_key_from_localized("不存在", "zh_hans") is None


def test_rarity_name_translates_key():
    assert vocab_loader.rarity_name("UNIQUE", "zh_hans") == "稀有宠物"


def test_blank_translation_is_not_indexed_for_reverse_lookup():
    # ko column is empty; empty string must not map back to a key
    assert vocab_loader.trait_key_from_localized("", "ko") is None
