# ChronosMatch — Cython Benchmark Results

## Test Configuration

- Orders per run: 10,000
- Expected trades per run: 5,000
- Implementation: Cython matching engine
- Measurement: Shared-memory writes and engine processing included

## Results

| Run     | Elapsed Time (seconds) | Throughput (orders/second) |
| ------- | ---------------------: | -------------------------: |
| 1       |               0.510829 |                  19,576.02 |
| 2       |               0.664395 |                  15,051.29 |
| 3       |               0.485086 |                  20,614.91 |
| Average |               0.553437 |                  18,414.07 |

## Summary

The three benchmark runs processed 10,000 submitted orders each, with 5,000 expected trades per run. Average measured throughput was approximately 18,414 orders per second.

These are preliminary local benchmark results, not a claim of production-grade high-frequency trading performance. Further testing is required for latency percentiles, sustained load, correctness under concurrency, and system resource usage.

## Latency Benchmark

- Orders submitted: 10,000
- Trades executed: 5,000
- Throughput: 19,997.97 orders/second
- Average matched-order latency: 259.71 ms
- p50 latency: 263.65 ms
- p95 latency: 468.04 ms
- p99 latency: 485.85 ms

Latency is measured from order submission to trade callback.
It includes queueing and engine polling delays and should not
be interpreted as pure matching-engine execution latency.

These results are a preliminary local benchmark, not a
production-grade HFT performance claim.

## Optimized Benchmark — Three Runs

| Run  | Elapsed (s) | Throughput (orders/s) | Avg Latency (ms) | p95 (ms) | p99 (ms) |
| ---- | ----------: | --------------------: | ---------------: | -------: | -------: |
| 1    |    0.496371 |              20146.22 |           240.77 |   462.32 |   479.44 |
| 2    |    0.684480 |              14609.64 |           347.08 |   643.28 |   665.39 |
| 3    |    0.516892 |              19346.40 |           257.76 |   473.87 |   498.29 |
| Mean |    0.565914 |              18034.09 |           281.87 |   526.49 |   547.71 |

Each run processed 10,000 orders and executed 5,000 trades.

The results show noticeable run-to-run variability. The shorter
polling interval has not yet demonstrated a consistent improvement
across repeated runs. Further controlled testing is needed.

Latency measures submission-to-trade-callback time, including
queueing and polling delays. It is not pure matching-engine latency.
