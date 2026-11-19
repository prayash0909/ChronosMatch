# ChronosMatch - Final Project Report

## 1. Project Overview
**Project:** ChronosMatch - Zero-Copy High-Frequency Trading Engine  
**Domain:** FinTech / Low-Latency Systems  
**Repository:** https://github.com/prayash0909/ChronosMatch

ChronosMatch is an educational prototype of a low-latency trading engine. It demonstrates order processing, price-time priority matching, partial fills, shared-memory communication, trade persistence, performance monitoring, and a browser-based dashboard.

## 2. Problem Statement
Trading systems need to process orders efficiently while preserving correctness. Common engineering concerns include matching latency, data transfer overhead, order-book consistency, partial execution, and reliable trade records.

ChronosMatch explores these concerns through a modular Python and Cython implementation.

## 3. Objectives
- Implement price-time priority order matching.
- Support FIFO execution and partial fills.
- Maintain independent order books for different symbols.
- Support order cancellation with symbol validation.
- Explore shared-memory communication between processes.
- Persist executed trades using SQLite.
- Expose engine state and metrics through an HTTP API.
- Display system activity in a browser dashboard.
- Validate correctness with automated tests and stress checks.

## 4. System Architecture
The project is organized into these main components:

| Component | Responsibility |
|---|---|
| Matching engine | Order submission, matching and cancellation |
| Order book | Price-time priority and pending orders |
| Cython engine | Compiled matching and stream-processing path |
| Shared-memory buffer | Producer-consumer communication |
| Market simulator | Generates sample order traffic |
| Trade ledger | Persists executed trades in SQLite |
| HTTP server | API endpoints and runtime state |
| Web dashboard | Displays trades and performance metrics |

The Python HTTP API and the separate shared-memory/Cython runner are distinct execution paths. They should not be described as one integrated live pipeline.

## 5. Matching Engine
The matching engine processes buy and sell orders according to price-time priority. Better prices receive priority, and orders at the same price follow FIFO ordering.

The implementation includes:
- Order submission.
- Matching and trade generation.
- Partial-fill handling.
- Independent books for different symbols.
- Cancellation by order ID, with optional symbol validation.

## 6. Multi-Symbol Support
Each trading symbol maintains an independent order book. Orders for one symbol do not match against orders for another symbol. Symbol handling is case-insensitive, and cancellation is scoped to the relevant symbol when supplied.

## 7. Shared-Memory and Cython Work
The shared-memory component provides a fixed-size buffer for passing order records between processes. The project includes wraparound, counter-safety, and recovery checks.

The Cython matching path explores compiled processing to reduce Python-level overhead. Historical benchmark measurements are retained in BENCHMARK_RESULTS.md and must be interpreted in their recorded test conditions.

## 8. Trade Persistence
The SQLite-backed TradeLedger records executed trades and provides methods for retrieving recent trades and trade analytics. This supports inspection of execution history independently of transient dashboard state.

## 9. API and Dashboard
The local service is available at `http://127.0.0.1:8000/ui/`.

Documented endpoints:
- `GET /api/health`
- `GET /api/state`
- `POST /api/orders`
- `POST /api/engine`
- `POST /api/reset`

The state endpoint reports runtime counters and performance information, including rolling five-second throughput and latency metrics. The dashboard presents these values.

The service binds to loopback by default. The engine status endpoint is a UI/service status flag; it does not start a separate matching thread.

## 10. Validation and Test Evidence
The latest recorded regression run on 19 November 2026 completed with:
- **74 tests passed**
- **5 subtests passed**
- Runtime: **4.82 seconds**

Additional verification includes:
- Price validation, including rejection of non-positive and non-finite values.
- Multi-symbol isolation and independent order books.
- Order cancellation and symbol validation.
- Rolling throughput-window calculations and metric reset.
- Shared-memory wraparound and counter checks.
- Producer/consumer shutdown and recovery scenarios.
- Million-order audit with checksum `500000500000`.

These results describe the recorded local test run. Re-run the suite before the final demonstration to confirm the current checkout.

## 11. Historical Performance Evidence
The repository contains historical Cython and shared-memory benchmark measurements. For example, a recorded event-based Cython run processed 10,000 orders in approximately 0.028 seconds, with a reported throughput of about 357,213 orders/second under that benchmark's conditions.

A separate shared-memory comparison recorded a 24.66% lower median time for the experimental buffer in its specific 20,000-write/20,000-read test.

These are historical, workload-specific measurements, not guaranteed production throughput or a fresh end-to-end benchmark of the complete system. See `BENCHMARK_RESULTS.md` for methodology and caveats.

## 12. Team and Contribution
ChronosMatch is a team project. This report describes the overall system and repository capabilities. Individual contributions should be presented according to the work actually completed by each team member.

## 13. Limitations
- Educational prototype, not a production exchange engine.
- No connection to a live exchange or real trading venue.
- Local HTTP service is intended for development and demonstration.
- Historical microbenchmarks are not directly comparable unless workload and environment match.
- Production deployment would require stronger concurrency guarantees, authentication, operational monitoring, security review, and extensive performance testing.

## 14. Future Enhancements
- Add authentication and role-based API access.
- Expand concurrency and fault-injection testing.
- Add reproducible end-to-end benchmark automation.
- Improve dashboard visualizations and historical analytics.
- Add deployment configuration and operational monitoring.

## 15. Conclusion
ChronosMatch demonstrates core concepts used in low-latency trading software: deterministic order matching, price-time priority, partial execution, symbol isolation, inter-process communication, persistence, API design, and performance observability. Automated tests and recorded audits provide evidence for the implemented functionality.
