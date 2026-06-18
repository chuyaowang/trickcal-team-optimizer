"""Regression tests for the web pet selector that need a Streamlit runtime.

Driven via streamlit's AppTest. Skipped automatically where streamlit isn't
installed.

Selections are seeded through ``session_state`` rather than by driving the
single-select ``st.pills`` palette: older Streamlit (the newest release that
still supports CI's Python 3.9) serializes a single-select button_group by
iterating ``self.value`` and calling ``format_func`` on each element. A scalar
string value (e.g. a pet name) iterates into characters, so ``format_func``
would look up ``pets_by_name['<char>']`` and ``KeyError``. Production never hits
this -- the palette's on_change callback resets its value to ``None`` after each
click, so no scalar is ever serialized -- and seeding state keeps this test
robust across Streamlit versions.
"""
import pytest

pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest

from src.data_loader.csv_loader import load_pets

APP = "src/ui/web_gui.py"


def test_switching_server_clears_selections_without_crashing():
    """Switching servers must clear selections and not KeyError on re-render.

    Selections are server-language-specific; ``on_server_change`` clears them,
    and the summary boxes defensively skip names absent from the new server.
    """
    raw_cn = load_pets(server="cn")[0]["name"]
    at = AppTest.from_file(APP).run(timeout=60)
    assert not at.exception, at.exception

    # Simulate cn-server selections (owned + borrowed).
    at.session_state["owned_set"] = [raw_cn]
    at.session_state["borrow_counts"] = {raw_cn: 1}

    # Switch to a different server: re-rendering with stale cn names must not
    # crash, and on_server_change must clear the selections.
    srv = [r for r in at.radio if r.key == "server"][0]
    srv.set_value("gl-cn").run(timeout=60)
    assert not at.exception, at.exception
    assert at.session_state["owned_set"] == []
    assert at.session_state["borrow_counts"] == {}