#!/usr/bin/env python3
"""Render a line chart of daily unique visitors from GoatCounter.

Fetches the full visitor history via the GoatCounter stats API and writes an
SVG line chart to assets/visitors.svg. Intended to run in CI; configured via
environment variables:

    GOATCOUNTER_TOKEN   API token with "Read statistics" permission (required)
    GOATCOUNTER_CODE    Site code / subdomain (default: michaelseelion)
    GOATCOUNTER_START   ISO date to start the history from (default: 2025-01-01)
    OUTPUT              Output SVG path (default: assets/visitors.svg)
"""

import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

CODE = os.environ.get("GOATCOUNTER_CODE", "michaelseelion")
TOKEN = os.environ.get("GOATCOUNTER_TOKEN")
START = os.environ.get("GOATCOUNTER_START", "2025-01-01")
OUTPUT = os.environ.get("OUTPUT", "assets/visitors.svg")

STATS_URL = f"https://{CODE}.goatcounter.com/api/v0/stats/total"

# Minimum x-axis span: when there's little data, pad the axis this many days
# to the right so a sparse chart (e.g. a single day) isn't cramped.
MIN_SPAN_DAYS = 90


def fetch_total():
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = f"{START}T00:00:00Z"
    end = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{STATS_URL}?start={start}&end={end}"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {TOKEN}"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_series(stats):
    """Return (days, counts) covering only the range that has visitor data.

    GoatCounter returns every day in the requested window, including zero-visit
    days, so we anchor the range to the first and last days that actually have
    visitors and zero-fill any gaps in between for a continuous line.
    """
    by_day = {
        datetime.strptime(s["day"], "%Y-%m-%d").date(): int(s.get("daily", 0))
        for s in stats
    }
    data_days = [d for d, c in by_day.items() if c > 0]
    if not data_days:
        return [], []
    start, end = min(data_days), max(data_days)
    days, counts = [], []
    cur = start
    while cur <= end:
        days.append(cur)
        counts.append(by_day.get(cur, 0))
        cur += timedelta(days=1)
    return days, counts


def render(days, counts, total):
    fig, ax = plt.subplots(figsize=(9, 3.2), dpi=120)

    if days:
        ax.plot(days, counts, color="#f4900c", linewidth=2,
                marker="o", markersize=4)
        ax.fill_between(days, counts, color="#f4900c", alpha=0.15)
        # Anchor to the first data day; pad the right out to MIN_SPAN_DAYS so a
        # sparse chart spans a few months instead of being cramped. Once data
        # covers more than that span, the axis just follows the data.
        left = days[0]
        right = max(days[-1], left + timedelta(days=MIN_SPAN_DAYS))
        ax.set_xlim(left - timedelta(days=1), right)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        fig.autofmt_xdate(rotation=0, ha="center")
    else:
        ax.text(0.5, 0.5, "No data yet", ha="center", va="center",
                transform=ax.transAxes, color="#888")
        ax.set_xticks([])

    ax.set_ylim(bottom=0)
    ax.set_ylabel("Unique visitors / day")
    ax.set_title(f"App visitors over time  ·  {total} total", loc="left",
                 fontsize=12, fontweight="bold")
    ax.grid(True, axis="y", linestyle="--", alpha=0.3)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    fig.tight_layout()
    os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
    fig.savefig(OUTPUT, format="svg", bbox_inches="tight")
    print(f"Wrote {OUTPUT} ({len(days)} days, {total} total visitors)")


def main():
    if not TOKEN:
        print("GOATCOUNTER_TOKEN is not set", file=sys.stderr)
        return 1
    data = fetch_total()
    days, counts = build_series(data.get("stats", []))
    render(days, counts, data.get("total", sum(counts)))
    return 0


if __name__ == "__main__":
    sys.exit(main())