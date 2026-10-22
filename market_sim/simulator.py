"""Synthetic market firehose for the local ChronosMatch prototype.

The target rate is a best-effort pacing goal, not a throughput guarantee.
A full IPC ring buffer applies back-pressure instead of dropping orders.
"""
import asyncio
import random
import time


class HighThroughputSimulator:
    def __init__(self, shared_buffer, target_orders_per_second=100_000, seed=None):
        if target_orders_per_second <= 0:
            raise ValueError("target_orders_per_second must be positive")
        self.buffer = shared_buffer
        self.target_orders_per_second = int(target_orders_per_second)
        self._interval = 1.0 / self.target_orders_per_second
        self._order_id = 50_000_000
        self._random = random.Random(seed)
        self.generated = 0
        self.backpressure_events = 0
        self.started_ns = None

    async def generate_market_ticks(self, shutdown_flag, max_orders=None, report_every=10_000):
        """Write mock orders until shutdown_flag[0] is true or max_orders is reached."""
        self.started_ns = time.perf_counter_ns()
        next_tick = time.perf_counter()
        print(f"[SIMULATOR] target={self.target_orders_per_second:,} orders/s; Ctrl+C to stop")
        try:
            while not shutdown_flag[0] and (max_orders is None or self.generated < max_orders):
                self._order_id += 1
                order = (
                    self._order_id,
                    round(self._random.uniform(150.00, 155.50), 2),
                    self._random.randint(1, 500),
                    self._random.choice((b"B", b"S")),
                )
                try:
                    self.buffer.write_order(*order)
                    self.generated += 1
                except BufferError:
                    self.backpressure_events += 1
                    # The consumer must make room before another write.
                    await asyncio.sleep(0.0005)
                    continue

                if report_every and self.generated % report_every == 0:
                    elapsed = (time.perf_counter_ns() - self.started_ns) / 1e9
                    rate = self.generated / elapsed if elapsed else 0
                    print(f"[SIMULATOR] generated={self.generated:,} rate={rate:,.0f}/s backpressure={self.backpressure_events:,}")

                next_tick += self._interval
                delay = next_tick - time.perf_counter()
                if delay > 0:
                    await asyncio.sleep(delay)
                else:
                    # Avoid a runaway catch-up loop when the machine is overloaded.
                    next_tick = time.perf_counter()
        finally:
            elapsed = (time.perf_counter_ns() - self.started_ns) / 1e9 if self.started_ns else 0
            rate = self.generated / elapsed if elapsed else 0
            print(f"[SIMULATOR] stopped generated={self.generated:,} elapsed={elapsed:.3f}s actual_rate={rate:,.0f}/s backpressure={self.backpressure_events:,}")
