---
title: NYC Taxi & Ride-Hail Data — 1.6 Billion Rides
description: >
  Interactive dashboard of every NYC yellow-cab, green-cab, Uber and Lyft trip
  since January 2020 — 1.6 billion rows of NYC TLC trip record data queried
  straight from the raw Parquet files by DuckDB, rebuilt nightly on GitHub
  Actions, served as a static page.
---

# 1.6 billion rides. One duck. Zero servers.

Every chart on this page is a SQL query running on **DuckDB** over the **raw
Parquet files** published by the [NYC Taxi & Limousine Commission](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) —
no warehouse, no ETL, no server. A GitHub Actions job re-downloads the data
and rebuilds the page every night, so when TLC publishes a new month, it shows
up here on its own.

<Grid cols=4>
<Counter data={kpis} column="trips" label="Trips analyzed" format="number" decimals=0 />
<Counter data={kpis} column="gb" label="Raw Parquet scanned" format="number" decimals=1 suffix=" GB" />
<Counter data={kpis} column="files" label="Parquet files" format="number" decimals=0 />
<Counter data={kpis} column="months" label="Months of history" format="number" decimals=0 />
</Grid>

## Taxis vs ride-hail since 2020

Six years of monthly trips, one line per service — the yellow cab, the green
cab, Uber and Lyft. Each line is that service's own volume, so the COVID-19
collapse in early 2020 and the long climb back read straight off the axis.

<LineChart data={monthly_by_service} x="month" y="trips" series="service" title="Monthly trips by service" />

<Ask data={monthly_by_service} inline replay="always">Write one flowing paragraph, in the voice of a data journalist, telling the story this chart shows: the COVID-19 collapse in early 2020, the slow recovery, and how Uber, Lyft and the yellow cab ended up splitting the market. Cite a few concrete numbers (trips, months, rough percentages). Do not use bullet points or a heading — just prose.</Ask>

Money and market share tell the same story from two more angles — who carries
the trips, and who collects the fares:

<Grid cols=2>
<ThemeRiver data={monthly_by_service} x="month" y="share_pct" series="service" title="Market share, % of trips" />
<BarChart data={monthly_by_service} x="month" y="revenue" series="service" stacked title="Rider spend per month" format="currency" decimals=0 />
</Grid>

<Ask data={monthly_by_service} inline replay="always">In one short paragraph of prose (no heading, no lists), describe how the share of trips and the monthly rider spend have shifted between the yellow cab and the ride-hail apps since 2020. Name the current market-share leader and roughly what fraction of trips it carries.</Ask>

Fares and tips are where the two worlds diverge most:

<Grid cols=2>
<LineChart data={monthly_by_service} x="month" y="avg_fare" series="service" title="Average base fare" format="currency" />
<BarChart data={tip_by_service} x="service" y="tip_pct" title="Average tip, % of fare (card / in-app)" format="number" decimals=1 suffix="%" />
</Grid>

<Ask data={monthly_by_service} inline replay="always">Write one short paragraph (prose only, no heading) on the tipping gap between taxis and ride-hail apps in this data. Note that cab tips are recorded only on card payments while Uber/Lyft tips are always in-app, so the comparison is imperfect — but the gap is still striking. Give the rough tip percentages for each.</Ask>

*A note on the comparison: cab "base fare" is the meter fare; Uber/Lyft is the
base passenger fare before fees. Cab tips are only recorded on card payments;
Uber/Lyft tips are always in-app — that's the honest reason the gap looks so brutal.*

## Under the microscope: the newest month

TLC publishes with a ~2-month lag; the freshest month on file is
<Value data={latest_summary} column="label" />, with
<Value data={latest_summary} column="trips" format="number" decimals=0 /> trips —
each one a row in the raw files queried below.

<BarChart data={daily_trips} x="day" y="trips" title="Every single day" />

<Grid cols=2>
<PieChart data={share_donut} x="service" y="trips" donut title="Who owned the street" />
<LineChart data={hourly_by_service} x="hour" y="trips" series="service" title="Trips by hour of day" />
</Grid>

<Ask data={share_donut,hourly_by_service} inline replay="always">Write one paragraph of prose (no heading, no lists) about the newest month: which service carried the most trips and roughly its share, and what the by-hour curve says about when New Yorkers actually ride — the morning and evening peaks and the late-night pattern.</Ask>

<HeatmapChart data={dow_hour_heatmap} x="hour" y="day" value="trips" title="When New York moves — weekday × hour" explain />

<Ask data={dow_hour_heatmap} inline replay="always">In one short paragraph of prose, describe the busiest weekday-and-hour combinations in this heatmap — the commuter peaks versus the Friday and Saturday late-night surge — as if narrating the rhythm of the city's week. No heading, no lists.</Ask>

<Grid cols=2>
<BarChart data={top_zones} x="zone" y="trips" horizontal title="Busiest pickup zones" />
<SankeyChart data={borough_flows} source="source" target="target" value="trips" title="Borough → borough flows" />
</Grid>

<Ask data={top_zones,borough_flows} inline replay="always">Write one closing paragraph of prose (no heading, no lists) on the geography of the newest month: which pickup zones top the list (note if the airports rank high), and what the borough-to-borough flows reveal about how much of the city's traffic begins and ends inside Manhattan.</Ask>

## The receipts

Every number above comes from these monthly aggregates — the raw output of the
history query, one row per service per month:

<Table data={receipts} title="Monthly stats by service"
       format="revenue=currency, avg_fare=currency"
       heatmap="trips,revenue,avg_fare,avg_miles,avg_minutes,tip_pct"
       page-size=12 sort="month desc" />

---

**How it's built** — the raw TLC Parquet files are downloaded as-is
(`scripts/fetch_data.py`), and every chart above is a plain SQL query in
`queries/` that reads those files directly with DuckDB's `read_parquet()` — no
tables to define, no ETL. [Dashdown](https://pypi.org/project/dashdown-md/)'s
`dashdown build` executes the queries once and bakes the results into this
static page; a GitHub Actions cron does that every night. The prose between the
charts is written by an LLM at build time from each query's result — commentary
that refreshes with the data.
