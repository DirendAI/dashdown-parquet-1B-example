---
title: 1.7 Billion Rides
description: >
  Every NYC yellow-cab, green-cab, Uber and Lyft trip since January 2020 —
  queried straight from the raw TLC Parquet files by DuckDB, rebuilt nightly
  on GitHub Actions, served as a static page.
---

Every chart on this page is a SQL query running on **DuckDB** over the **raw
Parquet files** published by the [NYC Taxi & Limousine Commission](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) —
no warehouse, no ETL, no server. A GitHub Actions job re-downloads the data
and rebuilds the page every night, so when TLC publishes a new month, it shows
up here on its own.

## The whole market

<Grid cols=4>
<Counter data={kpis} column="trips" label="Trips analyzed" format="number" decimals=0 />
<Counter data={kpis} column="gb" label="Raw Parquet scanned" format="number" decimals=1 suffix=" GB" />
<Counter data={kpis} column="files" label="Parquet files" format="number" decimals=0 />
<Counter data={kpis} column="months" label="Months of history" format="number" decimals=0 />
</Grid>

## Taxis vs ride-hail since 2020

<LineChart data={monthly_by_service} x="month" y="trips" series="service" stacked title="Monthly trips by service" />

<Ask data={monthly_by_service} label="What happened here?"
     ask="In 3-4 sentences, tell the story of NYC ground transport since 2020: the COVID collapse, the recovery, and how Uber, Lyft and the yellow cab split the market. Cite a few concrete numbers." />

<Grid cols=2>
<LineChart data={monthly_by_service} x="month" y="share_pct" series="service" title="Market share, % of trips" />
<LineChart data={monthly_by_service} x="month" y="revenue" series="service" stacked title="Rider spend per month" format="currency" decimals=0 />
</Grid>

<Grid cols=2>
<LineChart data={monthly_by_service} x="month" y="avg_fare" series="service" title="Average base fare" format="currency" />
<LineChart data={monthly_by_service} x="month" y="tip_pct" series="service" title="Tips, % of fare (card / in-app)" />
</Grid>

## Under the microscope: the newest month

TLC publishes with a ~2-month lag; the freshest month on file is
<Value data={latest_summary} column="label" />, with
<Value data={latest_summary} column="trips" format="number" decimals=0 /> trips —
each one a row in the raw files queried below.

<Grid cols=2>
<PieChart data={share_donut} x="service" y="trips" donut title="Who owned the street" />
<LineChart data={hourly_by_service} x="hour" y="trips" series="service" title="Trips by hour of day" />
</Grid>

<LineChart data={daily_by_service} x="day" y="trips" series="service" title="Every single day" />

<HeatmapChart data={dow_hour_heatmap} x="hour" y="day" value="trips" title="When New York moves — weekday × hour" explain />

<Grid cols=2>
<BarChart data={top_zones} x="zone" y="trips" horizontal title="Busiest pickup zones" />
<SankeyChart data={borough_flows} source="source" target="target" value="trips" title="Borough → borough flows" />
</Grid>

<Ask data={hourly_by_service,share_donut,top_zones}
     ask="Summarize this month in NYC ride data in 3 sentences: who dominated, when the city was busiest, and one detail a New Yorker would find fun." />

## The receipts

<Table data={monthly_by_service} title="Monthly stats by service"
       format="revenue=currency, avg_fare=currency" page-size=12 sort="month desc" />

---

**How it's built** — the raw TLC Parquet files are downloaded as-is
(`scripts/fetch_data.py`), a [Dashdown](https://pypi.org/project/dashdown-md/)
`parquet` source points DuckDB at them, and every chart above is a plain SQL
query in `queries/`. `dashdown build` executes the queries once and bakes the
results into this static page; a GitHub Actions cron does that every night.
