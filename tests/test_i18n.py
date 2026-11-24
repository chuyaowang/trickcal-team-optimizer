import pytest
from src.core.i18n import t

def test_translation_lookups():
    # Test English
    assert t('APP_TITLE', 'en') == "🐾 Globally Optimal Pet Dispatch Team Planner"
    assert t('RESULTS', 'en') == "📊 Calculation Results"
    
    # Test Chinese
    assert t('APP_TITLE', 'cn') == "🐾 全局最优宠物派遣方案计算器"
    assert t('RESULTS', 'cn') == "📊 计算结果"
    
    # Test fallback to Chinese for unknown language
    assert t('APP_TITLE', 'fr') == "🐾 全局最优宠物派遣方案计算器"
    
    # Test unknown key (returns key)
    assert t('UNKNOWN_KEY', 'en') == 'UNKNOWN_KEY'

def test_nested_server_names():
    # English server names
    en_servers = t('SERVER_NAMES', 'en')
    assert list(en_servers) == ['gl-cn', 'gl-en', 'gl-jp', 'kr']

    # Chinese server names
    cn_servers = t('SERVER_NAMES', 'cn')
    assert list(cn_servers) == ['gl-cn', 'gl-en', 'gl-jp', 'kr']


def test_every_ui_language_has_the_same_strings():
    from src.core.i18n import TRANSLATIONS
    assert set(TRANSLATIONS) == {'en', 'cn', 'jp'}
    keys = set(TRANSLATIONS['en'])
    for lang, strings in TRANSLATIONS.items():
        assert set(strings) == keys, lang
        assert set(strings['SERVER_NAMES']) == set(TRANSLATIONS['en']['SERVER_NAMES']), lang


def test_japanese_ui_strings():
    assert t('BORROW_TAG', 'jp') == ' (レンタル)'
    assert t('BORROW_TAG', 'cn') == ' (借)'
    assert t('SERVER_NAMES', 'jp')['gl-jp'] == 'グローバル版 (GL-JP)'
