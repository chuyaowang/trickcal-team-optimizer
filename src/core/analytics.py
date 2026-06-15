"""Best-effort visitor analytics via GoatCounter.

Records one pageview per browser session to a self-hosted GoatCounter
instance so app usage can be charted on the README. All network activity
runs in a daemon thread and swallows every error: analytics must never
slow down or break the app.
"""

import json
import os
import threading
import urllib.request

import streamlit as st

# GoatCounter site code (public; also appears in the README badge URL).
GOATCOUNTER_CODE = "michaelseelion"
_COUNT_URL = f"https://{GOATCOUNTER_CODE}.goatcounter.com/api/v0/count"
_TIMEOUT = 4  # seconds


def _get_token():
    """Read the API token from Streamlit secrets, then the environment."""
    try:
        token = st.secrets["GOATCOUNTER_TOKEN"]
        if token:
            return token
    except Exception:
        pass
    return os.environ.get("GOATCOUNTER_TOKEN")


def _header(headers, name):
    """Case-insensitive header lookup."""
    return headers.get(name) or headers.get(name.lower()) or headers.get(name.upper())


def _client_ip(headers):
    """Extract the real visitor IP from the proxy's X-Forwarded-For header."""
    xff = _header(headers, "X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return None


def _post(token, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _COUNT_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=_TIMEOUT).read()
    except Exception:
        pass  # analytics must never break the app


def track_visit(path="/app"):
    """Record one GoatCounter pageview per browser session (best-effort)."""
    if st.session_state.get("_gc_tracked"):
        return
    st.session_state["_gc_tracked"] = True

    token = _get_token()
    if not token:
        return

    try:
        headers = dict(st.context.headers)
    except Exception:
        headers = {}

    ip = _client_ip(headers)
    ua = _header(headers, "User-Agent")

    hit = {"path": path}
    # GoatCounter derives a unique-visitor session from hash(UA + IP + salt).
    # If we can't supply both, fall back to a sessionless pageview to avoid a
    # 400 error (it still counts, just without unique-visitor grouping).
    no_sessions = True
    if ip and ua:
        hit["ip"] = ip
        hit["user_agent"] = ua
        no_sessions = False

    payload = {"no_sessions": no_sessions, "hits": [hit]}
    threading.Thread(target=_post, args=(token, payload), daemon=True).start()