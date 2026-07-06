#!/usr/bin/env python3
"""Download the raw NYC TLC trip Parquet files the dashboard queries.

Three datasets: yellow cabs, green cabs, and FHVHV (Uber/Lyft — the
high-volume for-hire vehicles). Nothing is transformed: the files land in
data/trips/ exactly as TLC published them, and every dashboard query runs
straight over the raw Parquet with DuckDB.

- Probes CloudFront for each dataset's newest published month (TLC publishes
  with a ~2-month lag, so we walk back from the current month until a file
  answers).
- Downloads every month from --since to that newest month into data/trips/
  (files already on disk are skipped, so re-runs are incremental).
- Copies each dataset's newest month to data/latest/<dataset>.parquet — a
  stable path for the deep-dive queries, whatever month it actually is.
- Converts the taxi-zone lookup CSV to data/history/taxi_zones.parquet (once).

Usage:
  python scripts/fetch_data.py                    # 2020-01 -> today, ~43 GB (CI)
  python scripts/fetch_data.py --since 2026-03    # small window (local dev)
"""

from __future__ import annotations

import argparse
import os
import shutil
import ssl
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

# python.org macOS builds ship without root CAs wired up — use certifi's
# bundle when it's importable (it always is in CI, where pip installed it).
try:
    import certifi

    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # fall back to the system default trust store
    SSL_CTX = ssl.create_default_context()

ROOT = Path(__file__).resolve().parent.parent
TRIPS = ROOT / "data" / "trips"
TRIP_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/{dataset}_tripdata_{month}.parquet"
ZONES_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
HEADERS = {"User-Agent": "dashdown-duckdb-example/1.0"}
DATASETS = ["yellow", "green", "fhvhv"]
DEFAULT_SINCE = "2020-01"  # ~1.7B rows across the three datasets from here

# CloudFront rate-limits bursts with 403s — and from a datacenter runner,
# parallel workers trip it fast (and keep it tripped, since the survivors
# hammer on while one backs off). One patient stream still moves ~43 GB in
# ~10-15 min on a GitHub runner. Override locally with FETCH_WORKERS=4.
WORKERS = int(os.environ.get("FETCH_WORKERS", "1"))


def month_url(dataset: str, month: str) -> str:
    return TRIP_URL.format(dataset=dataset, month=month)


def month_seq(since: str, until: str) -> list[str]:
    y, m = map(int, since.split("-"))
    uy, um = map(int, until.split("-"))
    out = []
    while (y, m) <= (uy, um):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def shift_month(ym: str, delta: int) -> str:
    y, m = map(int, ym.split("-"))
    idx = y * 12 + (m - 1) + delta
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def url_exists(url: str, retries: int = 5) -> bool:
    """HEAD with backoff. CloudFront answers 403 both for 'missing' and for
    rate-limiting, so a 403 is retried with growing pauses before we trust it."""
    for attempt in range(retries):
        req = urllib.request.Request(url, method="HEAD", headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30, context=SSL_CTX):
                return True
        except urllib.error.HTTPError as e:
            if e.code in (403, 404) and attempt == retries - 1:
                return False
            time.sleep(5 * (attempt + 1))
        except urllib.error.URLError:
            time.sleep(5 * (attempt + 1))
    return False


def find_latest_month(dataset: str, max_back: int = 8) -> str:
    """Walk back from last month until a published file answers."""
    today = date.today()
    probe = f"{today.year:04d}-{today.month:02d}"
    for _ in range(max_back):
        probe = shift_month(probe, -1)
        if url_exists(month_url(dataset, probe)):
            return probe
    sys.exit(f"no published month found for {dataset} — CloudFront unreachable or rate-limited")


def download(url: str, dest: Path, retries: int = 8) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=900, context=SSL_CTX) as resp, \
                    open(tmp, "wb") as f:
                shutil.copyfileobj(resp, f, length=1 << 20)
            tmp.rename(dest)
            return
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
            tmp.unlink(missing_ok=True)
            if attempt == retries - 1:
                raise
            # a tripped CloudFront limiter can hold a 403 for minutes — wait it out
            wait = 30 * (attempt + 1)
            print(f"  {dest.name}: retry in {wait}s ({e})", flush=True)
            time.sleep(wait)


def fetch_zones() -> None:
    import duckdb

    out = ROOT / "data" / "history" / "taxi_zones.parquet"
    if out.exists():
        return
    csv = out.with_suffix(".csv")
    download(ZONES_URL, csv)
    duckdb.sql(f"COPY (SELECT * FROM read_csv_auto('{csv}')) TO '{out}' (FORMAT PARQUET)")
    csv.unlink()
    print(f"wrote {out.relative_to(ROOT)}")


def latest_marker(latest: dict[str, str]) -> str:
    """The canonical newest-month fingerprint, e.g. 'yellow=2026-05\\n…'.
    Written to data/latest/LATEST.txt on download and published into the build,
    so CI can compare 'what's live' against 'what TLC has now' with a string ==."""
    return "".join(f"{d}={m}\n" for d, m in latest.items())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--since", default=DEFAULT_SINCE, help="first month, YYYY-MM")
    ap.add_argument("--print-latest", action="store_true",
                    help="print the newest published month per dataset and exit "
                         "(HEAD probes only, no download) — used by the CI change check")
    args = ap.parse_args()

    latest = {d: find_latest_month(d) for d in DATASETS}
    if args.print_latest:
        print(latest_marker(latest), end="")
        return
    print("newest published month:", ", ".join(f"{d}={m}" for d, m in latest.items()))

    jobs = [(d, m) for d in DATASETS for m in month_seq(args.since, latest[d])
            if not (TRIPS / f"{d}_tripdata_{m}.parquet").exists()]
    print(f"{len(jobs)} file(s) to download")
    t0, done = time.time(), 0

    def fetch(job: tuple[str, str]) -> None:
        nonlocal done
        d, m = job
        download(month_url(d, m), TRIPS / f"{d}_tripdata_{m}.parquet")
        done += 1
        if done % 10 == 0:
            print(f"  {done}/{len(jobs)} files", flush=True)
        time.sleep(0.25)  # keep the request rate polite

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(fetch, jobs))  # list() re-raises worker exceptions

    size = sum(f.stat().st_size for f in TRIPS.glob("*.parquet"))
    print(f"data/trips/: {len(list(TRIPS.glob('*.parquet')))} files, "
          f"{size / 1e9:.1f} GB (downloaded in {(time.time() - t0) / 60:.1f} min)")

    latest_dir = ROOT / "data" / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    for d, m in latest.items():
        shutil.copyfile(TRIPS / f"{d}_tripdata_{m}.parquet", latest_dir / f"{d}.parquet")
    (latest_dir / "LATEST.txt").write_text(latest_marker(latest))
    print("stable copies:", ", ".join(f"{d}.parquet={m}" for d, m in latest.items()))

    fetch_zones()


if __name__ == "__main__":
    main()
