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
    assert en_servers['cn'] == "China Server (CN)"
    
    # Chinese server names
    cn_servers = t('SERVER_NAMES', 'cn')
    assert cn_servers['cn'] == "中国服 (CN)"
