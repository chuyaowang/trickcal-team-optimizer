"""Regression tests for the web pet selector that need a Streamlit runtime.

Driven via streamlit's AppTest. Skipped automatically where streamlit isn't
installed. Pills/segmented_control surface as ``button_group`` in AppTest, and
image-label pills must be driven by their RAW option value (not ``.options``,
which returns the formatted markdown).
"""
import pytest

pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest

from src.data_loader.csv_loader import load_pets

APP = "src/ui/web_gui.py"


def _bg(at, key):
    return [b for b in at.button_group if b.key == key][0]


def test_switching_server_clears_selections_without_crashing():
    """Selecting on one server then switching servers must not KeyError.

    Selections are server-language-specific; switching servers clears them.
    """
    raw_cn = load_pets(server="cn")[0]["name"]
    at = AppTest.from_file(APP).run(timeout=60)
    assert not at.exception, at.exception

    # Own a pet on the default (cn) server.
    _bg(at, "palette").set_value(raw_cn).run(timeout=60)
    assert at.session_state["owned_set"] == [raw_cn]

    # Switch to a different server: must not crash, selections cleared.
    srv = [r for r in at.radio if r.key == "server"][0]
    srv.set_value("gl-cn").run(timeout=60)
    assert not at.exception, at.exception
    assert at.session_state["owned_set"] == []
    assert at.session_state["borrow_counts"] == {}
