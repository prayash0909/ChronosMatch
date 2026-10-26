
import threading
import time
import statistics

from shared_memory.buffer import SharedMemoryBuffer
from matching_engine.engine import match_order_stream


def percentile(values, percent):
    if not values:
        return 0.0

    ordered = sorted(values)
    index = max(0, (len(ordered) * percent + 99) // 100 - 1)
    return ordered[min(index, len(ordered) - 1)]


def main():
    buffer = SharedMemoryBuffer()
    buffer.reset_buffer()

    shutdown = [False]
    order_timestamps = {}
    latencies_us = []

    timestamp_lock = threading.Lock()
    latency_lock = threading.Lock()
    all_trades_done = threading.Event()

    total_orders = 10000
    expected_latency_samples = total_orders

    def on_trade(buy_id, sell_id, price, quantity):
        completed_at = time.perf_counter_ns()
        samples = []

        # Read timestamps safely while the producer may be updating them.
        with timestamp_lock:
            for order_id in (buy_id, sell_id):
                submitted_at = order_timestamps.get(order_id)
                if submitted_at is not None:
                    samples.append(
                        (completed_at - submitted_at) / 1000
                    )

        with latency_lock:
            latencies_us.extend(samples)

            if len(latencies_us) >= expected_latency_samples:
                all_trades_done.set()

    engine_thread = threading.Thread(
        target=match_order_stream,
        args=(buffer, shutdown, on_trade),
        kwargs={"verbose": False},
        daemon=True,
    )

    try:
        engine_thread.start()
        time.sleep(0.1)

        start_time = time.perf_counter()

        for i in range(total_orders // 2):
            sell_id = 10000 + i
            buy_id = 20000 + i

            with timestamp_lock:
                order_timestamps[sell_id] = time.perf_counter_ns()

            buffer.write_order(sell_id, 100.0, 1, b"S")

            with timestamp_lock:
                order_timestamps[buy_id] = time.perf_counter_ns()

            buffer.write_order(buy_id, 100.0, 1, b"B")

        if not all_trades_done.wait(timeout=10):
            with latency_lock:
                received = len(latencies_us)

            raise TimeoutError(
                f"Expected {expected_latency_samples} latency samples, "
                f"received {received}"
            )

        elapsed = time.perf_counter() - start_time

        with latency_lock:
            latency_snapshot = list(latencies_us)

        if len(latency_snapshot) != expected_latency_samples:
            raise RuntimeError(
                f"Expected {expected_latency_samples} latency samples, "
                f"got {len(latency_snapshot)}"
            )

        throughput = total_orders / elapsed

        print("\n===== CYTHON BENCHMARK (EVENT-BASED) =====")
        print(f"Orders submitted: {total_orders}")
        print(f"Trades executed: {len(latency_snapshot) // 2}")
        print(f"Elapsed time: {elapsed:.6f} seconds")
        print(f"Throughput: {throughput:.2f} orders/second")
        print(f"Measured matched-order latencies: {len(latency_snapshot)}")
        print(f"Average latency: {statistics.mean(latency_snapshot):.2f} us")
        print(f"p50 latency: {percentile(latency_snapshot, 50):.2f} us")
        print(f"p95 latency: {percentile(latency_snapshot, 95):.2f} us")
        print(f"p99 latency: {percentile(latency_snapshot, 99):.2f} us")
        print(
            "Note: Completion uses an Event instead of 1 ms polling. "
            "Latency includes queueing and engine polling delays."
        )

    finally:
        shutdown[0] = True
        engine_thread.join(timeout=2)
        buffer.close()


if __name__ == "__main__":
    main()
