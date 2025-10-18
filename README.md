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

1. **Ingest latest data** from `mutual_fund_nav_history.parquet` and `mutual_fund_data.csv` into a harmonised business-day index.
2. **Forward-fill and resample NAVs** to the requested frequency (business days by default) while logging missing data coverage.
3. **Compute log returns** and basic descriptive statistics to flag stale or anomalous series.
4. **Apply Hodrick–Prescott (HP) detrending** and an exponential moving average smoother to separate trend, cycle, and noise components.
5. **Measure spectral power** within 30–730 day periodicities using a Hann window to identify dominant cyclical signatures.
6. **Score each scheme** on momentum, mean reversion, spectral strength, and drawdown resilience; the weights are configurable in `configs/default.yaml`.
7. **Detect candidate bottoms** when the cyclical z-score breaches −1.5 and the post-breach rebound turns positive.
8. **Construct ranking tables** combining scores and bottom detections, including metadata such as category and AMC.
9. **Backtest selections** across 3-, 6-, and 12-month horizons with configurable transaction costs and rebalance cadence.
10. **Persist artefacts and visualisations** (tables, JSON summaries, PNG plots) under `artifacts/`, caching expensive intermediate tensors for repeatable runs.

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
2. **Create a Python environment (3.10 or newer recommended)**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```
3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Verify data files** (`mutual_fund_data.csv`, `mutual_fund_nav_history.parquet`) are present or downloaded from the linked Kaggle sources.

Caching behaviour: the pipeline stores intermediate frames under `artifacts/cache` (configurable) and reuses them when `enable_caching` is `true`. Delete the cache directory to force a full recomputation.

Logging: runtime logging defaults to `INFO` level with structured console output (using `rich`). Increase verbosity with `--log-level DEBUG` or the corresponding configuration field.

Failure handling: non-critical steps (e.g., spectral fit for a single scheme) emit warnings and skip the offending asset, while fatal errors (file not found, schema mismatch) respect the `fail_fast` flag—set it to `false` to continue processing remaining schemes.

## 🧾 Configuration

Configuration files live under `configs/`. The provided [`configs/default.yaml`](configs/default.yaml) contains:

- **Data locations** (`nav_history_path`, `scheme_metadata_path`, `output_root`).
- **Preprocessing options** (frequency, fill method, log return toggle).
- **Trend/cycle parameters** (HP lambda, EMA span).
- **Spectral settings** (window type, period bounds, detrend flag).
- **Scoring weights** for the four composite metrics and normalisation method.
- **Bottom detection logic** (lookback, z-score threshold, rebound requirement).
- **Backtest horizons** and transaction assumptions.
- **Runtime controls** (caching directory, logging level, fail-fast toggle).

Modify or extend this YAML to suit alternative workflows, then reference it via the CLI.

## 🖥️ CLI Usage

The pipeline exposes a command-line interface that accepts a configuration file:

```bash
python -m pipeline.run --config configs/default.yaml
```

Common overrides:

```bash
# Increase logging verbosity and disable caching for a fresh run
python -m pipeline.run --config configs/default.yaml --log-level DEBUG --no-cache

# Point to a different NAV snapshot and emit outputs to a custom folder
python -m pipeline.run \
  --config configs/default.yaml \
  --nav-history data/new_nav_history.parquet \
  --output-root results/2024-06-01
```

The CLI validates configuration keys, surfaces warnings when defaults are applied, and writes a run summary (`run_metadata.json`) to the output directory for reproducibility.

## 📤 Outputs & Plots

Each execution produces the following structure under the configured `output_root` (defaults to `artifacts/`):

```
artifacts/
├── cache/                     # Optional cached parquet/npz intermediates
├── logs/                      # Timestamped structured logs
├── rankings/latest.csv        # Scheme-level composite ranking table
├── bottoms/detections.csv     # Detected cyclical bottoms with signal metadata
├── backtests/
│   ├── horizon_063d.csv       # Rolling 3-month backtest summary
│   ├── horizon_126d.csv       # Rolling 6-month backtest summary
│   └── horizon_252d.csv       # Rolling 12-month backtest summary
└── plots/
    ├── scheme_<code>_cycle.png   # Cycle vs. trend decomposition
    ├── scheme_<code>_spectra.png # Spectral density snapshots
    └── scoreboard.png            # Top-N ranking heatmap
```

Use these artefacts directly in dashboards or downstream portfolio construction workflows.

## 🗃️ Dataset Reference

Two core data files power the analysis:

1. **`mutual_fund_data.csv`** — Latest scheme snapshot with NAV, AMC, AUM, category, ISINs, launch/closure dates, and other metadata.
2. **`mutual_fund_nav_history.parquet`** — Daily historical NAV series for over 20 million observations across Indian mutual fund schemes.

Both files are refreshed daily through a Kaggle Notebook maintained by the dataset author. The Parquet file is best downloaded locally due to its size.

## 🤝 Contributing

Contributions that improve documentation, extend the pipeline, or add validation notebooks are welcome. Please open an issue describing your proposal before submitting a pull request.

## 🙏 Acknowledgements

- Data sourced from the **Association of Mutual Funds in India (AMFI)**.
- Dataset compiled and published via Kaggle by community contributors.
- **Always consult a financial adviser before making investment decisions.**

## 📄 License

This project is released under the [MIT License](https://opensource.org/licenses/MIT).
