# ChronosMatch - Final Demo Checklist

## Before the demo
- [ ] Activate the project virtual environment.
- [ ] Run `python -m pytest -q` and record the result.
- [ ] Run `git diff --check`.
- [ ] Confirm the Git branch and working tree.
- [ ] Ensure the SQLite database is available if showing trade history.

## Dashboard demonstration
- [ ] Start the local service using the command documented in README.md.
- [ ] Open `http://127.0.0.1:8000/ui/`.
- [ ] Show the dashboard metrics.
- [ ] Submit a valid order using the documented API/UI workflow.
- [ ] Show the updated order/trade state.
- [ ] Explain that throughput is a rolling five-second metric.
- [ ] Explain that zero throughput can be valid when no recent orders were processed.

## Technical explanation
- [ ] Explain price-time priority and FIFO.
- [ ] Demonstrate or explain partial fills.
- [ ] Explain independent symbol order books.
- [ ] Explain cancellation and symbol validation.
- [ ] Explain the separate Cython/shared-memory execution path.
- [ ] Explain SQLite trade persistence.
- [ ] Present benchmark figures with their workload and historical caveats.

## Final repository checks
- [ ] Confirm README.md and BENCHMARK_RESULTS.md are current.
- [ ] Confirm PROJECT_REPORT.md and presentation are committed.
- [ ] Confirm all intended commits are pushed to the project branch.
- [ ] Confirm GitHub shows the latest commit.

## Important limitations to disclose
- This is an educational prototype, not a live exchange.
- The local API and Cython shared-memory runner are separate paths.
- Historical benchmark figures are not production guarantees.
