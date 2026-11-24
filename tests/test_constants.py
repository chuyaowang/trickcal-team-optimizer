from src.core import constants


def test_server_lang_maps_each_server_to_one_language():
    assert constants.SERVER_LANG == {
        "gl-cn": "zh_hant",
        "gl-en": "en",
        "gl-jp": "ja",
        "kr": "ko",
    }


def test_normalize_server_maps_retired_or_missing_server_to_gl_cn():
    assert constants.normalize_server("cn") == "gl-cn"
    assert constants.normalize_server(None) == "gl-cn"
    assert constants.normalize_server("gl-en") == "gl-en"


def test_rarity_base_score_keyed_by_rarity_key():
    assert constants.RARITY_BASE_SCORE["NORMAL"] == 2
    assert constants.RARITY_BASE_SCORE["RARE"] == 2
    assert constants.RARITY_BASE_SCORE["UNIQUE"] == 3
    assert constants.RARITY_BASE_SCORE["LEGENDARY"] == 5