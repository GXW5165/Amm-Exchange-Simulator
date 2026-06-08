# AMM Exchange Simulator

AMM Exchange Simulator is a local, offline simulator for a constant-product automated market maker. It models a single X/Y liquidity pool using `x * y = k`, runs timestamped events, records every state transition, and exports analytical reports for DeFi mechanism study, course projects, and repeatable experiments.

The project does not connect to any blockchain node and does not handle real assets.

## What It Supports

| Area | Capabilities |
| --- | --- |
| AMM trading | X to Y and Y to X swaps, constant-product pricing, fee retention in the pool |
| Liquidity management | Add/remove liquidity, LP share minting and burning, initial LP ownership assignment |
| Simulation | Timestamp-ordered event execution, multi-user wallets, YAML-driven scenarios |
| Analytics | Slippage, impermanent loss, user PnL, LP fee income, LP APY, pool depth |
| Backtesting | Import historical price CSV data and generate synthetic swap events from price moves |
| Reports | CSV logs, JSON summaries, Excel workbooks, PNG charts, PDF experiment reports |
| Interfaces | Non-interactive CLI, interactive CLI menu, Streamlit Web UI |
| Experiments | Built-in scenario runs and parameter sweeps for fee and liquidity comparisons |

## Quick Start

```powershell
# Install dependencies
D:\miniconda3\envs\jrrg\python.exe -m pip install -r requirements.txt

# Run the default one-command demo
D:\miniconda3\envs\jrrg\python.exe main.py --demo

# Run the default config plus comparison scenarios
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/default.yaml --scenarios

# Open the interactive CLI menu
D:\miniconda3\envs\jrrg\python.exe main.py

# Start the Web UI
D:\miniconda3\envs\jrrg\python.exe -m streamlit run streamlit_app.py
```

If `python` already points to your intended environment, the shorter forms also work:

```bash
python main.py --demo
python -m streamlit run streamlit_app.py
python -m pytest -q
```

## Project Layout

```text
amm-exchange-simulator/
├── configs/
│   └── default.yaml                  # Default simulation config
├── data/
│   ├── sample_price_history.csv      # Backtesting sample data
│   ├── stable_market.csv
│   ├── trend_market.csv
│   ├── volatile_market.csv
│   ├── saved_configs/                # Web-saved user configs
│   └── output/                       # Generated outputs, ignored by Git
├── src/
│   ├── amm/                          # Swap engine and liquidity manager
│   ├── analytics/                    # Metrics, summaries, PDF reports
│   ├── application/                  # Runner, validation, scenarios, backtesting
│   ├── domain/                       # Pool, user, exceptions
│   ├── infrastructure/               # Config loading and file exporters
│   ├── interface/                    # CLI
│   ├── simulator/                    # Event model, queue, execution engine
│   ├── visualization/                # PNG chart generation
│   └── web/                          # Streamlit support helpers
├── tests/                            # Pytest suite
├── main.py                           # CLI entry point
├── streamlit_app.py                  # Streamlit Web entry point
├── requirements.txt
└── pytest.ini
```

## Architecture

The code is organized as a layered application:

| Layer | Responsibility |
| --- | --- |
| Domain | Core data models such as `Pool` and `User` |
| AMM | Constant-product swap and liquidity operations |
| Simulator | Event ordering, execution loop, result object |
| Application | Config-driven runs, validation, scenarios, backtesting, sweeps |
| Analytics | Slippage, IL, LP metrics, PnL, summaries, PDF report generation |
| Infrastructure | YAML loading, CSV/JSON/Excel exports |
| Interface / Web | CLI and Streamlit user workflows |

The important dependency direction is top-down: UI and application code call into the simulator and services; domain models stay independent.

## Core Model

For an X to Y swap:

```text
k = x * y
effective_dx = dx * (1 - fee_rate)
dy = y - k / (x + effective_dx)
```

The pool receives the full input amount, while pricing uses the fee-adjusted amount. This means fees remain in the pool and can increase `k`.

Slippage is calculated as:

```text
abs(execution_price - theoretical_price) / theoretical_price * 100
```

Impermanent loss uses the standard 50/50 pool formula:

```text
IL(r) = 2 * sqrt(r) / (1 + r) - 1
```

## Configuration

Simulations can be described in YAML. The default configuration is [configs/default.yaml](configs/default.yaml).

Supported event types:

| Event type | Required fields |
| --- | --- |
| `swap` | `direction` (`x_to_y` or `y_to_x`), `amount_in` |
| `add_liquidity` | `amount_x`, `amount_y` |
| `remove_liquidity` | `lp_share` |

Example:

```yaml
initial_reserve_x: 1000.0
initial_reserve_y: 1000.0
fee_rate: 0.003
initial_lp_owner: protocol

users:
  alice:
    balance_x: 500.0
    balance_y: 500.0
    lp_shares: 0.0

events:
  - timestamp: 1
    event_type: swap
    user_id: alice
    direction: x_to_y
    amount_in: 10.0
```

## Running From CLI

### One-command demo

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --demo
```

Expected output includes:

```text
[simulation] processed_events=9
[simulation] swap_events=7
[simulation] liquidity_events=2
[simulation] total_fees=0.900000
```

### Config-driven run

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/default.yaml
```

### Built-in comparison scenarios

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py --config configs/default.yaml --scenarios
```

This runs the base simulation and then generates scenario outputs under `data/output/scenarios/`.

### Interactive CLI

```powershell
D:\miniconda3\envs\jrrg\python.exe main.py
```

The menu supports pool initialization, swaps, liquidity changes, status inspection, and CSV export.

## Web Interface

Start Streamlit:

```powershell
D:\miniconda3\envs\jrrg\python.exe -m streamlit run streamlit_app.py
```

Open:

```text
http://localhost:8501
```

The Web UI has three workspaces.

### Default Config

Runs `configs/default.yaml` with one click. After running, the page shows:

- summary metrics
- event records
- user PnL
- detailed PnL breakdown
- chart gallery
- CSV, JSON, Excel, and PDF downloads

### Custom Simulation

Use this workspace to edit:

- initial pool reserves
- fee rate
- initial LP owner
- user balances and LP shares
- swap / add liquidity / remove liquidity events

Saved configs are stored in `data/saved_configs/`.

### Backtesting

Backtesting imports a historical price series and turns sufficiently large price changes into synthetic swap events.

CSV format:

```csv
timestamp,price_y_per_x
0,1.00
1,1.02
2,0.98
3,1.05
```

You can either upload a CSV file or select one of the bundled samples:

- `sample_price_history.csv`
- `stable_market.csv`
- `trend_market.csv`
- `volatile_market.csv`

Backtesting parameters:

| Parameter | Meaning |
| --- | --- |
| Initial X Reserve | Starting Token X reserve |
| Initial Y Reserve | Starting Token Y reserve |
| Fee Rate | AMM swap fee |
| Volatility Threshold | Minimum relative price move required to generate a synthetic trade |

Uploaded CSV data is parsed in memory and is not written to a shared repository file, so separate runs do not overwrite each other.

## Outputs

Default CLI outputs:

```text
data/output/logs/simulation.csv
data/output/results/summary.json
data/output/results/*.png
data/output/results/report.pdf
```

Web runs use isolated directories:

```text
data/output/web_runs/<run_id>/
├── simulation.csv
├── summary.json
├── simulation.xlsx
├── report.pdf
└── *.png
```

Scenario runs use:

```text
data/output/scenarios/<scenario_name>/
```

`data/output/` is ignored by Git because it contains generated artifacts.

## Reports

The simulator exports four report formats:

| Format | Content |
| --- | --- |
| CSV | Event-level execution log |
| JSON | Structured simulation summary |
| Excel | Multi-sheet workbook with events, summary, PnL, LP metrics, pool depth, parameters, charts |
| PDF | Presentation-style report with cover page, key metrics, analysis notes, charts, and event appendix |

## Testing

Run the full suite:

```powershell
D:\miniconda3\envs\jrrg\python.exe -m pytest -q
```

Current expected result:

```text
81 passed
```

The test suite covers:

- pool math
- liquidity operations
- simulator event execution
- validation
- analytics metrics
- scenario generation
- parameter sweeps
- visualization
- CLI demo mode
- Web support helpers
- historical backtesting
- PDF report generation

## Notes And Boundaries

- The simulator models one X/Y pool.
- It supports constant-product AMM behavior only.
- It is an offline educational and analytical tool.
- It does not connect to wallets, contracts, exchanges, or live market data.
- Arbitrage-specific event execution is not currently implemented as a supported event type.

## Requirements

- Python 3.10 or newer
- Dependencies listed in [requirements.txt](requirements.txt)
