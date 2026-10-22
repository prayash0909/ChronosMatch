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
- `run_engine.py`: streaming-engine runner.
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
python -m pip install --upgrade pip setuptools Cython pytest
```

Build the Cython extension:

```powershell
python setup.py build_ext --inplace
```

Run the automated test suite:

```powershell
python -m pytest -q
```

The latest recorded local test run completed with **9 passed**. Run the tests again after changing code or setting up a fresh environment; individual test and experiment scripts may also need to be run separately.

Run the basic matching-engine example:

```powershell
python main.py
```

Run the shared-memory producer/engine demo if the extension has been built and the environment is configured:

```powershell
python run_engine.py
```

Check each script's source and expected inputs before running it. Some helpers use a local SQLite database; local database files are intentionally excluded from Git.

## Open the UI

Open `ui/index.html` directly in a modern browser, or serve the repository root locally:

```powershell
python -m http.server 8000
```

Then visit `http://localhost:8000/ui/`.

The dashboard currently contains **demo-only** order-book values, reference metrics, and a browser-local simulated order form. It is **not connected** to the Python/Cython matching engine, SQLite ledger, broker, or live market data. Its counters and chart are illustrative, not live performance measurements.

## Benchmark notes

See [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md). Treat the results as preliminary measurements from this development environment. They do not establish production-level throughput, end-to-end latency, multi-process safety under all failure modes, or exchange readiness.

## Important limitations before production use

A real trading system would require substantially more engineering and validation, including concurrency and memory-ordering guarantees, robust process lifecycle and crash recovery, market-data and broker/exchange adapters, security, observability, risk limits, persistence/replay guarantees, and extensive stress/failure testing.

## License

No license has been added yet. Contact the repository owner before reusing this code outside the permissions granted by GitHub's default terms.
