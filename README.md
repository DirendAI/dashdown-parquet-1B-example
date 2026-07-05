# NYC Rides × DuckDB — 1.6 billion rows, zero warehouse

A one-page analytics dashboard over **every NYC yellow-cab, green-cab, Uber and
Lyft trip since January 2020 (~1.6 billion rows)**, queried straight from the
raw Parquet files the [NYC TLC](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
publishes — no warehouse, no ETL, no backend.

- **Engine:** DuckDB (in-memory), via [Dashdown](https://pypi.org/project/dashdown-md/) — every query reads the raw Parquet directly with `read_parquet()`
- **Data:** raw TLC Parquet, downloaded as published (`scripts/fetch_data.py`) — never transformed
- **Queries:** plain SQL files in [`queries/`](queries/) — the whole "pipeline" is `SELECT` statements
- **Serving:** `dashdown build` bakes a static site; GitHub Actions rebuilds it **every night**,
  so new TLC months appear automatically (they publish with a ~2-month lag)
- **AI:** `<Ask />` cards let Claude narrate the charts at build time (optional)

## Run it locally

```bash
pip install 'dashdown-md[mistral]'

# grab a small window (each fhvhv month is ~0.5 GB; the full 2020-01 window is ~43 GB)
python scripts/fetch_data.py --since 2026-01

dashdown serve .        # live dev server on http://127.0.0.1:8000
```

## Deploy on GitHub Pages

1. Push this repo to GitHub.
2. Repo **Settings → Pages → Source: GitHub Actions**.
3. (Optional) add a `MISTRAL_API_KEY` repo secret for the AI commentary —
   without it the site still builds, the Ask cards just show a muted note.

The [workflow](.github/workflows/build.yml) runs nightly (and on every push to
`main`): it downloads the raw Parquet (~43 GB), lets DuckDB crunch it during
`dashdown build`, and deploys the static result to Pages.
