# Indian Mutual Fund Cyclicality Analysis 📊

This repository bundles a daily-updated Indian mutual fund dataset together with a lightweight analysis pipeline for detecting
basic cyclical behaviour, ranking schemes, and stress-testing simple allocation ideas. The codebase ships with pure-Python shims
that emulate the small slice of the pandas, numpy, and yaml APIs used by the project so the toolkit runs without heavy binary
dependencies.

## Table of Contents

- [🔟 Methodology Overview](#-methodology-overview)
- [⚖️ Assumptions & Limitations](#️-assumptions--limitations)
- [⚙️ Setup](#️-setup)
- [🧾 Configuration](#-configuration)
- [🖥️ CLI Usage](#️-cli-usage)
- [📤 Outputs](#-outputs)
- [🗃️ Dataset Reference](#️-dataset-reference)
- [🤝 Contributing](#-contributing)
- [🙏 Acknowledgements](#-acknowledgements)
- [📄 License](#-license)

## 🔟 Methodology Overview

The CLI’s `report` command executes the simplified workflow implemented in `cyclicity.report.generate_reports`. At a high level
it:

1. **Loads NAV history** from the configured Parquet file, coercing scheme codes and timestamps into clean, sorted series.【F:src/cyclicity/report.py†L20-L34】
2. **Scores schemes** by walking each NAV series, computing simple percentage returns, and ranking the mean result as a proxy for
   overall performance.【F:src/cyclicity/report.py†L36-L58】
3. **Detects turning points** by flagging the global minimum and maximum NAV for every scheme as proxy trough/peak markers.【F:src/cyclicity/report.py†L60-L86】
4. **Backtests a naive strategy** that weights higher-ranked schemes more heavily when accumulating daily returns.【F:src/cyclicity/report.py†L88-L115】
5. **Produces bottom signals** by marking positive-scoring schemes with a single vote, yielding a minimal contrarian screen.【F:src/cyclicity/report.py†L117-L127】
6. **Exports artefacts**—summary, turning points, and backtest CSVs—while ensuring the destination folders exist.【F:src/cyclicity/report.py†L129-L172】

The repository retains the historical moving-average pipeline under `src/mf_analysis/` for users who prefer the legacy strategy.
Both tracks share the same lightweight dependency footprint.

## ⚖️ Assumptions & Limitations

- The simplified statistics rely on consecutive NAV observations; large gaps are filtered during ingestion.【F:src/cyclicity/report.py†L24-L34】
- Returns are calculated using simple percentage changes without compounding or cash-flow adjustments.【F:src/cyclicity/report.py†L40-L52】
- Turning points identify global extrema only; intra-cycle oscillations are not captured.【F:src/cyclicity/report.py†L60-L86】
- Backtests are long-only and ignore costs—interpret results as relative signals, not absolute forecasts.【F:src/cyclicity/report.py†L88-L115】
- Performance characteristics of the pure-Python shims on very large datasets have not been benchmarked; extend with care.【F:src/pandas/__init__.py†L1-L538】【F:src/numpy/__init__.py†L1-L392】

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
   This creates a `.venv/` folder and resolves all runtime and development dependencies declared in `pyproject.toml`. The
   dependency set is intentionally small because pandas, numpy, and yaml are provided through built-in shims under
   `src/pandas`, `src/numpy`, and `src/yaml`. Keep future contributions compatible with these modules unless you explicitly add
   the real third-party packages back into the environment.【F:src/pandas/__init__.py†L1-L538】【F:src/numpy/__init__.py†L1-L392】【F:src/yaml/__init__.py†L1-L90】
3. **(Optional) Update the NAV history snapshot**
   The repository ships with a compact sample at `data/mutual_fund_nav_history.parquet` so the pipeline can be executed out of
   the box. Replace it with the latest full snapshot using the same filename to reproduce production-scale analytics.

Logging defaults to `INFO` and can be tuned via the `logging` section of the configuration file—set a filename to persist logs
across runs.【F:configs/default.yml†L1-L7】【F:src/cyclicity/report.py†L137-L144】 The simplified workflow raises on missing data or
schema mismatches but otherwise proceeds scheme by scheme, skipping empty groups gracefully.【F:src/cyclicity/report.py†L24-L30】【F:src/cyclicity/report.py†L40-L58】

## 🧾 Configuration

Configuration lives under `configs/`:

- [`configs/default.yml`](configs/default.yml) drives the `report` pipeline. Key sections configure the input parquet path,
  logging preferences, and output file locations.【F:configs/default.yml†L1-L33】【F:src/cyclicity/report.py†L137-L172】
- [`configs/simple.yaml`](configs/simple.yaml) powers the moving-average workflow behind the `analyze` and `backtest` commands in
  `mf_analysis.pipeline` and `mf_analysis.backtest`. This path is helpful when comparing the legacy strategy against the
  simplified cyclicity report.【F:src/mf_analysis/pipeline.py†L1-L189】【F:src/mf_analysis/backtest.py†L1-L173】

Copy either file to a new path and tweak the parameters that matter for your study; pass the new path to the relevant CLI command
with `--config`.

## 🖥️ CLI Usage

Run commands through `uv run` to ensure dependencies resolve inside the managed virtual environment:

```bash
# Execute the simplified cyclicity reports (config defaults to configs/default.yml)
uv run python main.py report

# Run the moving-average analysis pipeline (optionally layer overrides afterward)
uv run python main.py analyze

# Backtest the moving-average signals, recomputing them first
uv run python main.py backtest --refresh
```

Key behaviours:

- `report` accepts a single `--config` path (defaulting to `configs/default.yml`). The simplified workflow uses only the shims and
  helpers bundled in `src/`.
- `analyze` and `backtest` start from `configs/simple.yaml` and apply any extra `--config` files as overrides in the order
  provided. These commands also honour `--schemes` to focus on specific AMFI codes.【F:src/mf_analysis/pipeline.py†L28-L54】
- All commands execute inside the managed `uv` environment—no manual activation is required.

## 📤 Outputs

`report` honours the directories specified in `configs/default.yml` and writes three CSV artefacts (summary, turning points, and
backtest results). Empty outputs are created as zero-byte files so downstream automation can rely on their presence. No plots are
produced in the dependency-light workflow.【F:src/cyclicity/report.py†L129-L170】

`analyze` and `backtest` continue to write to `outputs/analysis/` and `outputs/backtests/` respectively, matching the structure
defined in `configs/simple.yaml` and the behaviour of `mf_analysis.pipeline`. The tqdm progress bars degrade gracefully to a
no-op when the library is unavailable.【F:src/mf_analysis/pipeline.py†L11-L27】【F:src/mf_analysis/backtest.py†L11-L28】

## 🗃️ Dataset Reference

Two core data files power the analysis:

1. **`mutual_fund_data.csv`** — Latest scheme snapshot with NAV, AMC, AUM, category, ISINs, launch/closure dates, and other
   metadata.
2. **`data/mutual_fund_nav_history.parquet`** — Daily historical NAV series. A lightweight fixture is included for local testing;
   swap in the full dataset from Kaggle using the same filename to reproduce production-scale analytics.

Both files originate from a Kaggle Notebook maintained by the dataset author. The sample Parquet fixture in this repository keeps
the repository small; the authentic file is large (≈140 MB) and should be downloaded directly when running comprehensive
studies.

## 🤝 Contributing

Contributions that improve documentation, extend the pipeline, or add validation notebooks are welcome. Please open an issue
describing your proposal before submitting a pull request.

## 🙏 Acknowledgements

- Data sourced from the **Association of Mutual Funds in India (AMFI)**.
- Dataset compiled and published via Kaggle by community contributors.
- **Always consult a financial adviser before making investment decisions.**

## 📄 License

This project is released under the [MIT License](https://opensource.org/licenses/MIT).
