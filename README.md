# ChronosMatch

**ChronosMatch** is an educational prototype of a limit-order matching engine exploring price-time priority, partial fills, Cython integration, memory-mapped order buffers, and performance benchmarking.

> **Status:** Prototype / research project. It is not a production trading system and does not connect to a broker or live exchange.

## Features

- Buy/sell limit-order matching with price-time priority.
- Partial fills and remaining-quantity tracking.
- Cython-based matching-engine implementation and integration tests.
- Memory-mapped order buffer experiments, including FIFO, capacity, and wraparound checks.
- Benchmark scripts for the engine and buffer implementations.
- Trade-ledger persistence and verification helpers.
- Static trading-dashboard UI prototype in `ui/index.html`.

## Repository layout

- `order.py`, `order_book.py`: order model and in-memory order book.
- `matching_engine/`: matching engine core and Cython source.
- `shared_memory/`: order-buffer implementation and experiments.
- `run_engine.py`: shared-memory streaming-engine runner with per-trade nanosecond telemetry written to `latency_metrics.csv`.
- `market_sim/simulator.py`, `run_market_simulator.py`: asynchronous synthetic market firehose (best-effort target rate with ring-buffer back-pressure).
- `audit_ipc_million.py`: multi-process FIFO integrity/stress audit; default target is 1,000,000 orders.
- `test_market_simulator.py`: deterministic simulator tests.
- `ui_persistence/ledger.py`: local trade-ledger persistence.
- `test_*.py`: automated tests and focused test/experiment scripts.
- `benchmark_*.py`, `BENCHMARK_RESULTS.md`: performance experiments and reported results.
- `ui/index.html`: browser-based dashboard prototype.

## Requirements

- Python 3.14 was used in the current Windows development environment; other Python versions may require compatibility adjustments.
- pip, setuptools, Cython, and pytest.
- A compatible C/C++ compiler toolchain is needed to build the Cython extension on Windows.

## Windows / PowerShell setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip\npython -m pip install -r requirements.txt
```

Build the Cython extension:

```powershell
python setup.py build_ext --inplace
```

Run the automated test suite:

```powershell
python -m pytest -q
```

A previous local run completed with **9 passed** before the local API service tests were added. Run the current suite after updating the environment; individual benchmark and experiment scripts may also need to be run separately.

Run the basic matching-engine example:

```powershell
python main.py
```

Run the shared-memory producer/engine demo if the extension has been built and the environment is configured:

```powershell
python run_engine.py
```

In a separate terminal, run the asynchronous mock-market producer (the engine consumer must be running in another process with the same shared-memory tag):

```powershell
python run_market_simulator.py --rate 100000
```

To send a finite batch, use `python run_market_simulator.py --rate 100000 --orders 100000`. The rate is a best-effort target; actual throughput depends on the OS, buffer flushes, and consumer speed.

Run the multi-process FIFO stress audit (default one million orders; may take several minutes on Windows):

```powershell
python audit_ipc_million.py --orders 1000000 --timeout 300
```

Check each script's source and expected inputs before running it. Some helpers use a local SQLite database; local database files are intentionally excluded from Git.

## Run the dashboard with the Python engine

Install the dependencies and build the optional Cython stream extension as described above. Then start the local API and dashboard server from the repository root:

```powershell
python server.py
```

Open `http://127.0.0.1:8000/ui/`. The server binds to loopback only. The dashboard uses the Python `MatchingEngine` for submitted orders and reads the current in-memory order book plus recent SQLite ledger entries from the local API. Use Ctrl+C in the terminal to stop the server.

API endpoints:
- `GET /api/health` — local server health.
- `GET /api/state` — current order book, counters, recent persisted trades, and analytics.
- `POST /api/orders` — submit a validated limit order, with JSON fields `symbol`, `side`, `price`, and `quantity`.
- `POST /api/engine` — update the dashboard's running/paused status (this is a UI status flag, not a separate matching thread).
- `POST /api/reset` — clear the in-memory order book and counters; the saved SQLite trade ledger is retained.

You can still open `ui/index.html` directly for its standalone browser demo, but direct file mode cannot call the local Python API. The local server is a development integration only: it does not connect to a broker or live exchange, and it is not hardened for public network exposure. The Cython shared-buffer runner (`python run_engine.py`) is a separate experimental path from the HTTP API.

## Benchmark notes

See [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md). Treat the results as preliminary measurements from this development environment. They do not establish production-level throughput, end-to-end latency, multi-process safety under all failure modes, or exchange readiness.

## Important limitations before production use

A real trading system would require substantially more engineering and validation, including concurrency and memory-ordering guarantees, robust process lifecycle and crash recovery, market-data and broker/exchange adapters, security, observability, risk limits, persistence/replay guarantees, and extensive stress/failure testing.

## License

No license has been added yet. Contact the repository owner before reusing this code outside the permissions granted by GitHub's default terms.
