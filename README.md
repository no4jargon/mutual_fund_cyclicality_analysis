# Indian Mutual Fund Cyclicality Analysis 📊

This repository bundles a daily-updated Indian mutual fund dataset together with a configurable analysis pipeline for detecting cyclical behaviour, ranking schemes, and stress-testing contrarian or momentum allocation ideas.

## Table of Contents

- [🔟 Methodology Overview](#-methodology-overview)
- [⚖️ Assumptions & Limitations](#️-assumptions--limitations)
- [⚙️ Setup](#️-setup)
- [🧾 Configuration](#-configuration)
- [🖥️ CLI Usage](#️-cli-usage)
- [📤 Outputs & Plots](#-outputs--plots)
- [🗃️ Dataset Reference](#️-dataset-reference)
- [🤝 Contributing](#-contributing)
- [🙏 Acknowledgements](#-acknowledgements)
- [📄 License](#-license)

## 🔟 Methodology Overview

The default workflow implemented by the pipeline follows these ten stages:

1. **Ingest latest data** from `data/mutual_fund_nav_history.parquet` and `mutual_fund_data.csv` into a harmonised business-day index.
2. **Forward-fill and resample NAVs** to the requested frequency (business days by default) while logging missing data coverage.
3. **Compute log returns** and basic descriptive statistics to flag stale or anomalous series.
4. **Apply Hodrick–Prescott (HP) detrending** and an exponential moving average smoother to separate trend, cycle, and noise components.
5. **Measure spectral power** within 30–730 day periodicities using a Hann window to identify dominant cyclical signatures.
6. **Score each scheme** on momentum, mean reversion, spectral strength, and drawdown resilience; the weights are configurable in `configs/default.yaml`.
7. **Detect candidate bottoms** when the cyclical z-score breaches −1.5 and the post-breach rebound turns positive.
8. **Construct ranking tables** combining scores and bottom detections, including metadata such as category and AMC.
9. **Backtest selections** across 3-, 6-, and 12-month horizons with configurable transaction costs and rebalance cadence.
10. **Persist artefacts and visualisations** (tables, JSON summaries, PNG plots) under `outputs/`, caching expensive intermediate tensors for repeatable runs.

## ⚖️ Assumptions & Limitations

- The HP-filter lambda and EMA span are tuned for daily business data; extreme illiquidity or highly seasonal funds may require recalibration.
- Spectral analysis assumes regularly spaced observations. Schemes with long missing stretches are automatically excluded from spectral scoring.
- Backtests are long-only and do not include taxes, exit loads, or cash drag. Interpret projected returns as relative signals, not absolute forecasts.
- Strategy metrics depend on historical NAV fidelity. Corporate actions or scheme mergers reflected late in the source files can introduce artefacts.
- Default rankings treat schemes independently; category- or AMC-level capacity constraints must be handled externally.

## ⚙️ Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/mutual_fund_cyclicality_analysis.git
   cd mutual_fund_cyclicality_analysis
   ```
2. **Install dependencies with [uv](https://docs.astral.sh/uv/)**
   ```bash
   uv sync
   ```
   This creates a `.venv/` folder and resolves all runtime and development dependencies declared in `pyproject.toml`.
3. **(Optional) Update the NAV history snapshot**
   The repository ships with a compact sample at `data/mutual_fund_nav_history.parquet` so the pipeline can be executed out of the box.
   Replace it with the latest full snapshot from Kaggle by overwriting the same path if you want production-scale results.

Caching behaviour: the pipeline stores intermediate frames under `artifacts/cache` (configurable) and reuses them when `enable_caching` is `true`. Delete the cache directory to force a full recomputation.

Logging: runtime logging defaults to `INFO` level with structured console output (using `rich`). Increase verbosity with `--log-level DEBUG` or the corresponding configuration field.

Failure handling: non-critical steps (e.g., spectral fit for a single scheme) emit warnings and skip the offending asset, while fatal errors (file not found, schema mismatch) respect the `fail_fast` flag—set it to `false` to continue processing remaining schemes.

## 🧾 Configuration

Configuration files live under `configs/`. The provided [`configs/default.yaml`](configs/default.yaml) contains:

- **Data locations** (`metadata`, `nav_history`).
- **Signal construction** windows for detrending and rolling z-score normalisation.
- **Backtest thresholds** for entries, exits, and transaction costs.
- **Output directories** for tables, plots, and time-series exports.
- **Logging** defaults (level, format, timestamp style).

Modify or extend this YAML to suit alternative workflows, then reference it via the CLI.

## 🖥️ CLI Usage

The pipeline exposes a command-line interface that accepts a configuration file:

```bash
# Run the analysis pipeline
uv run main.py analyze --config configs/default.yaml

# Run the backtest (refresh ensures the latest signals are generated)
uv run main.py backtest --config configs/default.yaml --refresh
```

Key behaviours:

- All commands execute inside the managed `uv` environment—no manual activation is required.
- Use `--schemes 100033 100034` to restrict the run to specific scheme codes present in `mutual_fund_data.csv`.
- Logs default to INFO level; override by adding `--log-level DEBUG` after the sub-command.

## 📤 Outputs & Plots

Each execution produces the following structure under the configured `output_root` (defaults to `outputs/`):

```
outputs/
├── analysis/
│   ├── tables/
│   │   ├── fund_signals.csv      # Scheme-level signal history
│   │   └── fund_summary.csv      # Latest scores per scheme
│   └── plots/
│       └── top_fund_scores.png   # Signal trajectories for leading funds
└── backtests/
    ├── backtest_timeseries.csv   # Strategy daily performance
    └── backtest_summary.csv      # Aggregate statistics per scheme
```

Use these artefacts directly in dashboards or downstream portfolio construction workflows.

## 🗃️ Dataset Reference

Two core data files power the analysis:

1. **`mutual_fund_data.csv`** — Latest scheme snapshot with NAV, AMC, AUM, category, ISINs, launch/closure dates, and other metadata.
2. **`data/mutual_fund_nav_history.parquet`** — Daily historical NAV series. A lightweight fixture is included for local testing; swap in the full dataset from Kaggle using the same filename to reproduce production-scale analytics.

Both files originate from a Kaggle Notebook maintained by the dataset author. The sample Parquet fixture in this repository keeps the repository small; the authentic file is large (≈140 MB) and should be downloaded directly when running comprehensive studies.

## 🤝 Contributing

Contributions that improve documentation, extend the pipeline, or add validation notebooks are welcome. Please open an issue describing your proposal before submitting a pull request.

## 🙏 Acknowledgements

- Data sourced from the **Association of Mutual Funds in India (AMFI)**.
- Dataset compiled and published via Kaggle by community contributors.
- **Always consult a financial adviser before making investment decisions.**

## 📄 License

This project is released under the [MIT License](https://opensource.org/licenses/MIT).
10. **Persist artefacts and visualisations** (tables, JSON summaries, PNG plots) under `outputs/`, caching expensive intermediate tensors for repeatable runs.
