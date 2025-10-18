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

The CLI’s `report` command executes the advanced workflow implemented in `cyclicity.report.generate_reports`. At a high level it:

1. **Loads and resamples NAV history** from `data/mutual_fund_nav_history.parquet`, filtering out schemes without sufficient history and caching the tidy monthly panel for reuse between runs.【F:src/cyclicity/io.py†L18-L78】
2. **Detrends log NAVs** with a Hodrick–Prescott (HP) filter (or an alternate method specified in the configuration) to isolate cyclical residuals from the secular trend.【F:src/cyclicity/detrend.py†L15-L60】
3. **Estimates spectral strength** for the residual series using either Welch or Lomb–Scargle periodograms within a configurable frequency band to identify dominant periodicities.【F:src/cyclicity/report.py†L19-L113】
4. **Fits harmonic regressions** at the dominant period to quantify how well a sinusoidal model explains the detrended signal.【F:src/cyclicity/report.py†L67-L113】
5. **Tracks instantaneous cycles** through Hilbert transforms and a state-space cycle model to derive coherence and persistence diagnostics.【F:src/cyclicity/report.py†L95-L147】
6. **Detects turning points** in the Hilbert-derived cycle and constructs trough-focused bottom signals with guardrails to limit false positives.【F:src/cyclicity/report.py†L122-L162】
7. **Votes aggregate cyclicality scores** by combining spectrum, harmonic, Hilbert, state-space, and turning-point metrics using configurable weights and minimum-cycle requirements.【F:src/cyclicity/report.py†L153-L162】
8. **Backtests trough detections** over forward holding windows to provide hit rates and forward-return distributions.【F:src/cyclicity/report.py†L139-L162】【F:src/cyclicity/backtest.py†L11-L59】
9. **Exports artefacts**—summary tables, turning-point logs, backtest results, and per-scheme cycle plots—while optionally caching intermediate metrics for inspection or reuse.【F:src/cyclicity/report.py†L164-L210】

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

Caching behaviour: when `cache.enabled` is set in the configuration (on by default for the advanced workflow) the pipeline stores intermediate frames under the configured directory (defaults to `cache/`). Remove that directory to force a full recomputation.【F:configs/default.yml†L52-L55】【F:src/cyclicity/io.py†L21-L38】

Logging: runtime logging defaults to `INFO` and can be tuned via the `logging` section of the relevant configuration file—set a filename to persist logs across runs.【F:configs/default.yml†L1-L5】【F:src/cyclicity/report.py†L54-L64】

Failure handling: per-scheme errors are logged and skipped so a single bad NAV series does not abort the run; missing files or schema mismatches still raise exceptions early.【F:src/cyclicity/report.py†L125-L161】

## 🧾 Configuration

Configuration lives under `configs/` and now distinguishes the two workflows exposed by the CLI:

- [`configs/default.yml`](configs/default.yml) drives the advanced `report` pipeline. Key sections mirror the dataclasses in `cyclicity`:
  - `io`: parquet location and minimum history per scheme.【F:configs/default.yml†L1-L9】【F:src/cyclicity/io.py†L18-L78】
  - `detrend`, `spectrum`, `harmonic`, `hilbert`, and `state_space`: knobs for the time-series transforms applied to the detrended cycle.【F:configs/default.yml†L7-L33】【F:src/cyclicity/report.py†L57-L122】
  - `scoring.guardrails` and `scoring.weights`: voting thresholds for the final cyclicality score.【F:configs/default.yml†L33-L41】【F:src/cyclicity/report.py†L153-L162】
  - `backtest` and `report`: forward-return horizon and output locations.【F:configs/default.yml†L41-L52】【F:src/cyclicity/report.py†L139-L210】
  - `cache`: toggle and directory for reusing expensive intermediates.【F:configs/default.yml†L52-L55】【F:src/cyclicity/io.py†L21-L38】
- [`configs/simple.yaml`](configs/simple.yaml) retains the lightweight moving-average workflow behind the `analyze`/`backtest` commands. Use it as a starting point if you only need the basic detrend/z-score strategy implemented in `mf_analysis.pipeline`.

Copy either file to a new path and tweak the parameters that matter for your study; pass the new path to the relevant CLI command with `--config`.

## 🖥️ CLI Usage

The CLI now exposes both workflows; run commands through `uv run` to ensure dependencies are resolved:

```bash
# Execute the advanced cyclicity reports (config defaults to configs/default.yml)
uv run python main.py report

# Run the simple moving-average analysis pipeline (optionally layer overrides afterward)
uv run python main.py analyze

# Backtest the simple pipeline, recomputing signals first
uv run python main.py backtest --refresh
```

Key behaviours:

- `report` accepts a single `--config` path (defaulting to `configs/default.yml`). The advanced workflow manages its own logging according to that file.
- `analyze` and `backtest` start from `configs/simple.yaml` and apply any extra `--config` files as overrides in the order provided. These commands also honour `--schemes` to focus on specific AMFI codes.
- All commands execute inside the managed `uv` environment—no manual activation is required.

## 📤 Outputs & Plots

Outputs depend on the command you run:

- `report` honours the directories specified in `configs/default.yml` and produces:

  ```
  outputs/
  ├── csv/
  │   ├── cyclicity_summary.csv   # Combined scores, dominant periods, vote counts
  │   ├── turning_points.csv      # Dated peaks/troughs per scheme (may be empty if none detected)
  │   └── backtest_results.csv    # Forward-return samples for each voted trough
  └── plots/
      └── <scheme_code>_cycle.png # Trend, cycle, and turning points for every analysed fund
  ```

  When caching is enabled, additional JSON metrics appear under the configured cache directory for quick diagnostics.【F:src/cyclicity/report.py†L164-L210】

- `analyze` and `backtest` continue to write to `outputs/analysis/` and `outputs/backtests/` respectively, matching the structure defined in `configs/simple.yaml` and the behaviour of `mf_analysis.pipeline`.

These artefacts feed easily into dashboards or downstream allocation studies.

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
