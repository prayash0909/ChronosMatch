# ChronosMatch - Cython Benchmark Results

## 1. Test Configuration

- Orders per run: 10,000
- Expected trades per run: 5,000
- Implementation: Cython matching engine
- Measurement: Shared-memory writes and engine processing
- Environment: Local Windows development machine

## 2. Historical Baseline Benchmark

| Run     | Elapsed Time (seconds) | Throughput (orders/second) |
| ------- | ---------------------: | -------------------------: |
| 1       |               0.510829 |                  19,576.02 |
| 2       |               0.664395 |                  15,051.29 |
| 3       |               0.485086 |                  20,614.91 |
| Average |               0.553437 |                  18,414.07 |

These historical runs processed 10,000 submitted orders each, with 5,000 expected trades per run.

## 3. Historical Latency Benchmark

- Orders submitted: 10,000
- Trades executed: 5,000
- Throughput: 19,997.97 orders/second
- Average matched-order latency: 259.71 ms
- p50 latency: 263.65 ms
- p95 latency: 468.04 ms
- p99 latency: 485.85 ms

Latency includes queueing and engine polling delays. It is not pure matching-engine execution latency.

## 4. Historical Optimized Benchmark

| Run  | Elapsed (s) | Throughput (orders/s) | Avg Latency (ms) | p95 (ms) | p99 (ms) |
| ---- | ----------: | --------------------: | ---------------: | -------: | -------: |
| 1    |    0.496371 |             20,146.22 |           240.77 |   462.32 |   479.44 |
| 2    |    0.684480 |             14,609.64 |           347.08 |   643.28 |   665.39 |
| 3    |    0.516892 |             19,346.40 |           257.76 |   473.87 |   498.29 |
| Mean |    0.565914 |             18,034.09 |           281.87 |   526.49 |   547.71 |

These results showed run-to-run variability. They are retained as historical measurements.

## 5. Latest Event-Based Cython Benchmark

- Orders submitted: 10,000
- Trades executed: 5,000
- Elapsed time: 0.027995 seconds
- Throughput: 357,213.02 orders/second
- Measured matched-order latency samples: 10,000
- Average latency: 14,023.59 us
- p50 latency: 13,990.80 us
- p95 latency: 17,759.30 us
- p99 latency: 18,108.10 us

The benchmark uses an Event for completion instead of 1 ms polling. Timestamp dictionary access is protected by a lock.

These numbers represent one local run. Repeated runs are required to establish a reliable performance baseline. Throughput and latency measurements may vary with scheduling, polling, and system load.

## 6. Named mmap Buffer Comparison

### Test Configuration

- Operations per run: 20,000 writes and 20,000 reads
- Runs per implementation: 5
- Original implementation: Named mmap with per-operation flush calls
- Experimental implementation: Named mmap without per-operation flush calls
- Validation: Order ID, price, quantity, and side checked
- Execution order: Alternated between implementations

### Latest Controlled Benchmark Results

| Run    | Original mmap (seconds) | Experimental mmap (seconds) |
| ------ | ----------------------: | --------------------------: |
| 1      |                  0.0283 |                      0.0211 |
| 2      |                  0.0283 |                      0.0214 |
| 3      |                  0.0283 |                      0.0215 |
| 4      |                  0.0285 |                      0.0213 |
| 5      |                  0.0285 |                      0.0218 |
| Median |                  0.0283 |                      0.0214 |

The experimental buffer's median execution time was approximately 24.66% lower than the original buffer's median in this local microbenchmark.

All 20,000 orders were verified in each run.

An earlier benchmark recorded a 34.80% reduction. The latest measurements are recorded above because benchmark results vary between runs.

This microbenchmark result does not establish an equivalent improvement in overall ChronosMatch throughput or latency.

## 7. Multiprocess FIFO Test

Latest reported result:

- Status: PASS
- Orders verified: 5,000
- Order IDs: Sequential and correct

The test confirmed FIFO order verification and shared-buffer visibility. The reported run did not demonstrate guaranteed simultaneous producer-consumer overlap, so further concurrency stress testing is required.

## 8. Regression Tests

Latest reported test result:

- 14 tests passed
- 5 subtests passed
- Runtime: 3.54 seconds

## 9. Limitations and Next Steps

- These are preliminary local benchmark results, not a claim of production-grade high-frequency trading performance.
- The buffer comparison measures a specific write/read microbenchmark, not the complete matching engine.
- Latency includes queueing and engine polling delays.
- Repeat full-engine benchmarks several times before claiming stable throughput or latency improvements.
- Perform genuine concurrent producer-consumer stress testing before considering a production buffer replacement.
- Continue validating matching correctness and resource usage under sustained load.

## 7. Latest Verification Run

Date: 2026-10-25
Environment: Local Windows development machine

### Regression Tests

- Result: 14 passed, 5 subtests passed
- Runtime: 3.94 seconds

### Buffer Microbenchmark

Five runs were performed for each implementation, alternating execution order.

| Metric | Original mmap | Experimental mmap |
|---|---:|---:|
| Median time | 0.0361 seconds | 0.0284 seconds |

- Measured median time reduction: 21.35%
- All 20,000 orders were verified in each run.
- This is a local microbenchmark result, not proof of an equivalent improvement in end-to-end engine performance.

### Cython Matching Engine Benchmark

- Orders submitted: 10,000
- Trades executed: 5,000
- Elapsed time: 0.026501 seconds
- Throughput: 377,347.10 orders/second
- Measured matched-order latency samples: 10,000
- Average latency: 12,818.99 microseconds
- p50 latency: 12,096.10 microseconds
- p95 latency: 16,095.90 microseconds
- p99 latency: 16,305.00 microseconds

Completion was measured using a threading Event. Latency includes queueing and engine polling delays. These figures represent one local run and may vary between runs.

### Multiprocess FIFO Verification

- Orders verified: 5,000
- Order IDs: sequential and correct
- Result: PASS

The test observed the consumer reading orders before the producer signalled completion. This does not independently prove simultaneous read/write operations.

### Limitations

These results are preliminary local measurements. They do not establish production-grade high-frequency trading performance. Repeated runs under controlled conditions and further concurrency testing are needed.
