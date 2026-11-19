# ChronosMatch - Benchmark Results and Verification

## 1. Scope and Environment

ChronosMatch is an educational matching-engine and shared-memory research prototype.

- Environment: Local Windows development machine
- Language: Python with Cython components
- Areas measured: Matching-engine throughput, latency, shared-memory IPC, and data integrity
- Important: Historical benchmark figures below are not measurements from the latest verification date.

All performance results are environment-dependent. They should not be treated as production trading-system guarantees.

## 2. Historical Cython Matching-Engine Benchmarks

### 2.1 Historical Baseline

| Run | Elapsed time (seconds) | Throughput (orders/second) |
|---|---:|---:|
| 1 | 0.510829 | 19,576.02 |
| 2 | 0.664395 | 15,051.29 |
| 3 | 0.485086 | 20,614.91 |
| Average | 0.553437 | 18,414.07 |

Each run processed 10,000 submitted orders, with 5,000 expected trades.

### 2.2 Historical Latency Measurement

- Orders submitted: 10,000
- Trades executed: 5,000
- Throughput: 19,997.97 orders/second
- Average matched-order latency: 259.71 ms
- p50 latency: 263.65 ms
- p95 latency: 468.04 ms
- p99 latency: 485.85 ms

Latency includes queueing and engine polling delays. It is not pure matching-engine execution time.

### 2.3 Historical Optimized Runs

| Run | Elapsed (s) | Throughput (orders/s) | Average latency (ms) | p95 (ms) | p99 (ms) |
|---|---:|---:|---:|---:|---:|
| 1 | 0.496371 | 20,146.22 | 240.77 | 462.32 | 479.44 |
| 2 | 0.684480 | 14,609.64 | 347.08 | 643.28 | 665.39 |
| 3 | 0.516892 | 19,346.40 | 257.76 | 473.87 | 498.29 |
| Mean | 0.565914 | 18,034.09 | 281.87 | 526.49 | 547.71 |

These runs showed variability and are retained as historical measurements.

### 2.4 Historical Event-Based Cython Run

- Orders submitted: 10,000
- Trades executed: 5,000
- Elapsed time: 0.027995 seconds
- Throughput: 357,213.02 orders/second
- Matched-order latency samples: 10,000
- Average latency: 14,023.59 microseconds
- p50 latency: 13,990.80 microseconds
- p95 latency: 17,759.30 microseconds
- p99 latency: 18,108.10 microseconds

Completion used a threading Event instead of 1 ms polling. Timestamp dictionary access was protected by a lock. This is a single local run, not a repeatable performance guarantee.

A separate historical run recorded:

- Elapsed time: 0.026501 seconds
- Throughput: 377,347.10 orders/second
- Average latency: 12,818.99 microseconds
- p50 latency: 12,096.10 microseconds
- p95 latency: 16,095.90 microseconds
- p99 latency: 16,305.00 microseconds

This was also a single local run. Latency includes queueing and engine polling delays.

## 3. Shared-Memory IPC Benchmarks

### 3.1 Named mmap Flush Comparison

Test configuration:

- Operations per run: 20,000 writes and 20,000 reads
- Runs per implementation: 5
- Original implementation: Named mmap with per-operation flush calls
- Experimental implementation: Named mmap without per-operation flush calls
- Validation: Order ID, price, quantity, and side
- Execution order: Alternated between implementations

| Run | Original mmap (seconds) | Experimental mmap (seconds) |
|---|---:|---:|
| 1 | 0.0283 | 0.0211 |
| 2 | 0.0283 | 0.0214 |
| 3 | 0.0283 | 0.0215 |
| 4 | 0.0285 | 0.0213 |
| 5 | 0.0285 | 0.0218 |
| Median | 0.0283 | 0.0214 |

The experimental implementation recorded approximately 24.66% lower median execution time in this specific local microbenchmark. All 20,000 orders were verified in each run.

This result does not establish an equivalent improvement in complete engine throughput or latency.

### 3.2 Day 13 Performance Experiments

Recorded results:

- No-lock buffer median throughput: 347,224 orders/second.
- Lock-based buffer median throughput: 70,678 orders/second.
- Both variants passed FIFO, payload, and checksum validation.
- Flush benchmark median: 0.0317 seconds with flushes and 0.0239 seconds without flushes.
- Recorded median time reduction: 24.51%.
- Data-integrity checks passed.

These are results of specific local experiments, not a general recommendation to remove synchronization. Correctness and concurrency guarantees must take priority over speed.

### 3.3 Million-Order IPC Audit

Recorded audit results:

- Orders verified: 1,000,000
- Total elapsed time: 17.360 seconds
- Throughput: 57,602 orders/second
- Checksum: 500000500000
- FIFO validation: PASS
- Payload validation: PASS
- Checksum validation: PASS
- Producer-consumer overlap validation: PASS

The audit verified the complete one-million-order sequence and its integrity. The measured throughput applies to this audit workload and should not be compared directly with the separate Cython matching-engine benchmark.

### 3.4 Day 14 Shared-Memory Safety and Recovery

Recorded stress and recovery checks:

- Wraparound stress: 10,000 orders.
- Ring-buffer capacity in the stress test: 4.
- Wraparound cycles: 2,500.
- Final write counter: 10,000.
- Final read counter: 10,000.
- Counter inconsistency checks: PASS.
- Producer-crash recovery: recovered orders [1, 2, 3].
- Consumer-crash recovery: remaining orders [3, 4].
- Stale-buffer reset: write counter 0, read counter 0.

These tests exercise selected recovery and wraparound scenarios. They do not prove correctness under every possible process crash or hardware failure.

## 4. Multiprocess FIFO Verification

A separate 5,000-order test verified sequential order IDs and FIFO visibility.

- Orders verified: 5,000
- Sequential order IDs: PASS
- FIFO verification: PASS

The earlier run did not independently guarantee simultaneous producer-consumer overlap. The million-order audit has a separate recorded overlap validation result.

## 5. Functional and API Verification

The project includes automated checks for:

- Price-time priority and FIFO matching.
- Partial order fills and remaining quantities.
- Independent order books for different symbols.
- Case-insensitive symbol handling.
- Symbol-isolated matching and cancellation.
- Cancellation by order ID, with optional symbol validation.
- Rejection of invalid prices, including zero, negative, NaN, infinity, and out-of-range values.
- Invalid submissions not consuming order IDs.
- Rolling five-second throughput calculation.
- Removal of expired throughput timestamps.
- Resetting performance counters and latency measurements.

The API exposes health, state, order-submission, engine-status, and reset endpoints. The browser dashboard displays live API performance metrics. A zero throughput reading is valid when no orders were processed in the recent five-second window.

## 6. Latest Regression Verification - 19 November 2026

Environment: Local Windows development machine.

- Regression tests: 74 passed.
- Subtests: 5 passed.
- Runtime: 4.82 seconds.
- Result: PASS.

The test suite was run after the API validation, performance-metrics, dashboard, and matching-engine changes.

The dashboard was also checked against the local API. Its throughput uses a rolling five-second window, and its average latency is measured from processing activity since reset.

No new full-engine performance benchmark is claimed for 19 November 2026. The Cython and IPC performance figures in this document remain historical measurements.

## 7. Limitations

- These measurements are preliminary local development results.
- Benchmark figures depend on machine load, process scheduling, Python/Cython versions, and workload.
- The mmap comparison measures a specific write/read workload, not the entire matching engine.
- Matching latency includes queueing and polling in the recorded tests.
- A passing stress test does not prove safety under every possible concurrency or crash scenario.
- The project is not connected to a broker or live exchange and is not production-ready.

## 8. Future Engineering Work

Further work before any production use would include:

- Repeated and controlled full-engine benchmarks.
- More extensive concurrent producer-consumer and crash testing.
- Explicit synchronization and memory-ordering guarantees.
- Stronger persistence, replay, and recovery guarantees.
- Broker/exchange adapters, security, risk controls, and operational monitoring.
- Independent review and extensive load and failure testing.
