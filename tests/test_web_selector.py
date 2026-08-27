"""Regression tests for the web pet selector that need a Streamlit runtime.

Driven via streamlit's AppTest. Skipped automatically where streamlit isn't
installed.

Selections are seeded through ``session_state`` rather than by driving the
single-select ``st.pills`` palette: older Streamlit (the newest release that
still supports CI's Python 3.9, currently 1.50.0) serializes a single-select
button_group by iterating ``self.value`` and calling ``format_func`` on each
element. A scalar string value (e.g. a pet name) iterates into characters, so
``format_func`` would look up ``pets_by_name['<char>']`` and ``KeyError``.
Production never hits this -- the palette's on_change callback resets its
value to ``None`` after each click, so no scalar is ever serialized -- and
seeding state keeps this test robust across Streamlit versions.

That same old ButtonGroup._widget_state code path runs on *every* AppTest
``.run()`` after the first, for *every* button_group on the page, regardless
of whether the test touches it -- it has to reserialize each widget's current
value to replay the run. All three single-select pills on this page (palette,
owned_box, borrow_box) sit at their steady-state value of ``None`` (nothing
selected) most of the time, and iterating ``None`` raises ``TypeError``, not
``KeyError``. So any second ``.run()`` against this app crashes on old
Streamlit unless those widgets' test-side values are forced to an empty list
first; see ``_workaround_none_valued_button_groups`` below. Streamlit >=1.51
(Python >=3.10 only) rewrote ButtonGroup to handle single-select values
correctly -- ``None`` there means no selection and serializes fine -- and
would itself break if fed an empty list (it treats that as a literal
selected value, not "nothing selected"), so the workaround only applies to
the old class.
"""
import pytest

pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest

from src.data_loader.csv_loader import load_pets

# Relative to this file, not the repo root: Streamlit <1.61 resolved a
# relative AppTest.from_file() path against the process's cwd first (which
# happened to be the repo root under pytest, so a repo-root-relative path
# worked); >=1.61 dropped that and always resolves against the file that
# calls from_file() -- i.e. this one, in tests/. A path relative to here
# resolves correctly under both.
APP = "../src/ui/web_gui.py"


def _workaround_none_valued_button_groups(at):
    """Dodge the old-Streamlit button_group bug described above.

    Only the pre-1.51 ButtonGroup class needs this: it lacks
    ``_is_single_select`` and crashes serializing a ``None`` value. The
    fixed class carries that attribute and handles ``None`` natively, so it
    must be left alone (feeding it ``[]`` would break it the other way).
    """
    for bg in at.button_group:
        if not hasattr(bg, "_is_single_select") and at.session_state[bg.key] is None:
            bg.set_value([])


def test_switching_server_clears_selections_without_crashing():
    """Switching servers must clear selections and not KeyError on re-render.

    Selections are server-language-specific; ``on_server_change`` clears them,
    and the summary boxes defensively skip names absent from the new server.
    """
    # The app defaults to the gl-cn server; seed selections from it, then switch
    # to a different server (cn), whose pet names differ (Simplified vs
    # Traditional Chinese).
    raw_default = load_pets(server="gl-cn")[0]["name"]
    at = AppTest.from_file(APP).run(timeout=60)
    assert not at.exception, at.exception
    assert at.session_state["server"] == "gl-cn"

    # Simulate gl-cn selections (owned + borrowed).
    at.session_state["owned_set"] = [raw_default]
    at.session_state["borrow_counts"] = {raw_default: 1}

    _workaround_none_valued_button_groups(at)

    # Switch to a different server: re-rendering with stale names must not
    # crash, and on_server_change must clear the selections.
    srv = [r for r in at.radio if r.key == "server"][0]
    srv.set_value("cn").run(timeout=60)
    assert not at.exception, at.exception
    assert at.session_state["owned_set"] == []
    assert at.session_state["borrow_counts"] == {}