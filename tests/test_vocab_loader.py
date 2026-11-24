from src.data_loader import vocab_loader


def test_trait_name_translates_key_to_language():
    assert vocab_loader.trait_name("KIND", "ja") == "配慮"
    assert vocab_loader.trait_name("KIND", "en") == "Kind"


def test_trait_key_from_localized_is_reverse_of_trait_name():
    assert vocab_loader.trait_key_from_localized("配慮", "ja") == "KIND"
    assert vocab_loader.trait_key_from_localized("Kind", "en") == "KIND"


def test_trait_key_from_localized_returns_none_for_unknown():
    assert vocab_loader.trait_key_from_localized("不存在", "ja") is None


def test_rarity_name_translates_key():
    assert vocab_loader.rarity_name("UNIQUE", "ja") == "希少"
    assert vocab_loader.rarity_name("LEGENDARY", "ja") == "伝説"


def test_blank_translation_is_not_indexed_for_reverse_lookup():
    # ko column is empty; empty string must not map back to a key
    assert vocab_loader.trait_key_from_localized("", "ko") is None
