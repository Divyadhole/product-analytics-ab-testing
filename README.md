# Product Analytics & A/B Testing Platform

[![View Live Dashboard](https://img.shields.io/badge/View_Live_Dashboard-9FE870?style=for-the-badge&logo=github&logoColor=111827)](https://divyadhole.github.io/product-analytics-ab-testing/)

**[Open the interactive executive dashboard →](https://divyadhole.github.io/product-analytics-ab-testing/)**

An interview-ready product analytics case study that answers a concrete business question:

> **Should an e-commerce company ship a redesigned checkout progress experience?**

The project starts with raw, event-level behavioral data and produces a statistically defensible product decision. It demonstrates SQL modeling, funnel analysis, segmentation, experiment design, data quality, Python automation, and executive communication.

## Executive result

The simulated treatment changes the checkout experience after a shopper adds an item to their cart. The analysis measures whether it improves purchase conversion without hiding device-level behavior.

The published dashboard is available at **[divyadhole.github.io/product-analytics-ab-testing](https://divyadhole.github.io/product-analytics-ab-testing/)**.

Run the pipeline to calculate the final result from reproducible data:

```bash
python3 run_pipeline.py
open reports/experiment_report.html
```

No external libraries, API keys, or database server are required.

## What this demonstrates

- **Advanced SQL:** CTEs, conditional aggregation, reusable views, `NULLIF`, indexes, and dimensional segmentation
- **Product analytics:** acquisition attributes, behavioral events, conversion funnels, RPU, AOV, and device cuts
- **Experimentation:** deterministic assignment data, two-proportion z-test, confidence interval, practical lift, and a shipping rule
- **Experiment guardrails:** sample-ratio-mismatch detection, pre-test power calculation, planned MDE, and daily stability checks
- **Analytics engineering:** raw-to-modeled workflow, repeatable builds, quality assumptions, and tests
- **Communication:** a self-contained executive dashboard with a clear recommendation

## Architecture

```text
Reproducible generator
        │
        ▼
Raw CSV event tables
  users · assignments · events · orders
        │
        ▼
SQLite analytics warehouse
        │
        ├── user_funnel
        ├── funnel_summary
        ├── experiment_summary
        ├── segment_results
        ├── acquisition_results
        └── daily_experiment_results
        │
        ▼
Statistical test + executive HTML report
```

## Data model

| Table | Grain | Purpose |
|---|---|---|
| `users` | One row per user | Acquisition and device dimensions |
| `assignments` | One row per user and experiment | Control/treatment exposure |
| `events` | One row per behavioral event | Session-to-purchase funnel |
| `orders` | One row per order | Revenue outcomes |

The generated dataset contains 12,000 users and uses a fixed seed. The treatment effect is intentionally small enough to require statistical testing rather than visual guesswork.

## Experiment design

- **Unit of randomization:** user
- **Primary metric:** user-level purchase conversion
- **Secondary metrics:** revenue per user and average order value
- **Diagnostic dimensions:** device type
- **Hypothesis:** the checkout progress treatment increases purchase conversion
- **Decision rule:** ship only when lift is positive and the two-sided p-value is below 0.05
- **Quality gates:** assignment balance passes at 1% significance and observed sample size meets the planned 2.5 percentage-point MDE

The confidence interval uses the unpooled standard error for the difference in proportions. The hypothesis test uses the pooled standard error under the null hypothesis.

The platform also performs a sample-ratio-mismatch test before interpreting outcomes. A statistically significant allocation imbalance can indicate broken randomization or exposure logging, so it blocks shipping even when conversion appears positive.

## Project structure

```text
product-analytics-ab-testing/
├── data/
│   └── raw/                    # Generated source tables (gitignored)
├── reports/                    # HTML dashboard and JSON result
├── sql/
│   ├── 01_data_quality.sql
│   ├── 02_funnel_model.sql
│   └── 03_experiment_metrics.sql
├── src/
│   ├── generate_data.py
│   ├── build_database.py
│   ├── experiment.py
│   └── report.py
├── tests/
├── Makefile
└── run_pipeline.py
```

## Run and test

Requires Python 3.10 or newer.

```bash
# Build data, models, statistical result, and dashboard
make run

# Run unit and integration tests
make test

# Remove generated artifacts
make clean
```

The main output is `reports/experiment_report.html`. The machine-readable statistical result is saved to `reports/experiment_result.json`, modeled tables are exported under `data/processed/`, and the SQLite warehouse is saved to `data/product_analytics.db`.

## SQL questions answered

1. Where does the largest funnel drop occur?
2. Did treatment change cart creation or checkout completion?
3. What are conversion, revenue per user, and average order value by variant?
4. Does the direction of the effect remain consistent across devices?
5. Are both variants represented and is every analyzed user assigned exactly once?
6. Is allocation consistent with the planned 50/50 split?
7. Is the experiment sufficiently powered for its planned minimum detectable effect?
8. Is the effect stable across experiment days and acquisition channels?

## Honest limitations

- The data is synthetic, although its schema and effect sizes mimic a real product event stream.
- This is a fixed-horizon analysis; repeatedly checking the p-value would inflate false positives.
- Device cuts are diagnostic and are not separately powered experiments.
- Revenue is right-skewed; a production analysis should add bootstrap confidence intervals and guardrail metrics such as refunds and latency.
- Sample-ratio mismatch, bot filtering, novelty effects, and exposure logging require additional checks in a live experiment.

## Interview walkthrough

1. Start with the shipping decision in the HTML report.
2. Explain the event-table grain and user-level randomization.
3. Walk through `sql/02_funnel_model.sql` to show how events become one user-level outcome row.
4. Explain absolute lift, relative lift, p-value, and confidence interval in plain language.
5. Close with limitations and the instrumentation checks you would add in production.
