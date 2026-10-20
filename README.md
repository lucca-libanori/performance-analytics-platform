# Performance Analytics Data Platform

## Overview

This project is a data analytics platform designed to track, process, and analyze the performance of recurring decisions with quantifiable, measurable outcomes, built and demonstrated around sports betting for my case, but adaptable to any domain where you place capital repeatedly and need to track results over time: trading, poker, prediction markets, or any personal investment strategy.

It simulates a real-world data pipeline, transforming raw entries into structured insights through an ETL process, a relational database, and an interactive dashboard.

The system evaluates performance using key metrics such as profit, ROI, hit rate, drawdown, and risk-adjusted return (Sharpe), with interactive filtering and visualization built for exploration, not just reporting. A Monte Carlo risk simulation then tests whether the worst drawdown observed was unusual or just normal variance.

**Adapting it to another domain** (e.g., trades instead of bets) mainly means renaming a handful of fields — the pipeline, database design, and analytics layer stay the same.

---

## Tech Stack

* **Python** (Pandas, SQLAlchemy)
* **PostgreSQL**
* **SQL**
* **Streamlit**
* **Plotly** (interactive visualizations)
* **CSV (data ingestion)**

---

## Features

* Data ingestion from CSV files, with validation and cleaning
* Automated ETL pipeline using Python
* Structured relational database (PostgreSQL)

* KPI calculations:

  * Total Profit
  * ROI (%)
  * Hit Rate (%)
  * Total Stake
  * Max Drawdown & Drawdown Duration

* Interactive dashboard with filters:

  * Sport / Category
  * Sportsbook / Source
  * Date range

* Analytical views:

  * Profit over time by Sportsbook
  * Bankroll evolution over time
  * Drawdown over time
  * Total Risk vs Return (cumulative ROI vs. rolling volatility)
  * Performance breakdown.

* Monte Carlo risk simulation (dedicated page):

  * Reshuffles the settled entries thousands of times and records the maximum drawdown of each run
  * Compares the observed drawdown against the simulated distribution (median, 95th percentile)
  * Estimates the risk of ruin for a configurable bankroll size
  * Reproducible results through a configurable random seed

* Full entry management: add, edit, and delete records directly from the dashboard

---

## Project Structure
```
performance-analytics-platform/
│
├── data/
│   └── bets.csv
│
├── database/
│   └── schema.sql
│
├── sql/
│   └── metrics.sql
│
├── pages/
│   ├── 1_Bet_Management.py
│   ├── 2_Analytics.py
│   └── 4_Risk_Simulation.py
│
├── app.py
├── load_bets.py
└── README.md
```

---

## How to Run

### 1. Clone the repository

```
git clone https://github.com/lucca-libanori/performance-analytics-platform.git
cd performance-analytics-platform
```

### 2. Install dependencies

```
pip install streamlit pandas numpy plotly sqlalchemy psycopg2-binary python-dotenv
```

### 3. Set up PostgreSQL

* Create a database (default name used in this project: `betting_analytics`)

* Run the SQL schema:

```
database/schema.sql
```

### 4. Configure environment variables

Create a `.env` file in the project root with your database credentials:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=betting_analytics
DB_USER=your_user
DB_PASSWORD=your_password
```

### 5. Load the data

```
python load_bets.py
```

### 6. Run the dashboard

```
streamlit run app.py
```

If that command doesn't work, try:

```
python -m streamlit run app.py
```

---

## Dashboard Metrics

The dashboard provides:

* Total number of entries
* Total profit
* ROI (%)
* Hit rate (%)
* Total stake
* Max Drawdown and Drawdown Duration

It also includes breakdowns by:

* Sport / Category
* Sportsbook / Source

And visualizations such as:

* Profit over time by category
* Bankroll evolution over time
* Drawdown over time
* Risk vs. Return (cumulative ROI and rolling volatility)
* Distribution of simulated maximum drawdowns vs. the observed one (Monte Carlo)

---

## Risk Simulation (Monte Carlo)

The **Risk Simulation** page answers one question: *was the worst drawdown a matter of bad luck, or is it normal for this history?*

1. The profit of every settled entry (win, loss, void) is taken in chronological order.
2. The entries are randomly reordered (same entries, same total profit, different sequence) and the maximum drawdown of that new order is computed.
3. Step 2 is repeated thousands of times (5,000 by default), producing a distribution of possible maximum drawdowns.
4. The observed drawdown is placed on that distribution, with the median, the 95th percentile, and the share of simulations that were as bad or worse.

Settings available in the sidebar: number of simulations, random seed, and bankroll size (used only to estimate the risk of ruin).

**Limitations:** the simulation assumes entries are independent and interchangeable, so streaks, changes in stake, and changes in strategy are ignored. The drawdown on this page is computed entry by entry, so it can be slightly larger than the one shown on the Analytics page, which uses daily totals.