from src.core import constants


def test_server_lang_maps_each_server_to_one_language():
    assert constants.SERVER_LANG == {
        "cn": "zh_hans",
        "gl-cn": "zh_hant",
        "gl-en": "en",
        "kr": "ko",
    }


def test_rarity_base_score_keyed_by_rarity_key():
    assert constants.RARITY_BASE_SCORE["NORMAL"] == 2
    assert constants.RARITY_BASE_SCORE["RARE"] == 2
    assert constants.RARITY_BASE_SCORE["UNIQUE"] == 3
    assert constants.RARITY_BASE_SCORE["LEGENDARY"] == 5