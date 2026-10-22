
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
    processed_trades = []
    order_timestamps = {}
    latency_lock = threading.Lock()

    def on_trade(buy_id, sell_id, price, quantity):
        completed_at = time.perf_counter_ns()

        with latency_lock:
            # Measure from submission of each matched order
            # to the callback reporting its trade.
            for order_id in (buy_id, sell_id):
                submitted_at = order_timestamps.get(order_id)
                if submitted_at is not None:
                    processed_trades.append(
                        (buy_id, sell_id, price, quantity,
                         (completed_at - submitted_at) / 1000)
                    )

    engine_thread = threading.Thread(
    target=match_order_stream,
    args=(buffer, shutdown, on_trade),
    kwargs={"verbose": False},
    daemon=True
   )

    try:
        engine_thread.start()
        time.sleep(0.1)

        total_orders = 10000
        start_time = time.perf_counter()

        # Alternate SELL and BUY orders at the same price.
        for i in range(total_orders // 2):
            sell_id = 10000 + i
            buy_id = 20000 + i

            with latency_lock:
                order_timestamps[sell_id] = time.perf_counter_ns()
                buffer.write_order(sell_id, 100.0, 1, b"S")

                order_timestamps[buy_id] = time.perf_counter_ns()
                buffer.write_order(buy_id, 100.0, 1, b"B")

        expected_trades = total_orders // 2
        deadline = time.monotonic() + 10

        while True:
            with latency_lock:
                trade_count = len(processed_trades)

            if trade_count >= expected_trades * 2:
                break

            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Expected {expected_trades} trades, "
                    f"received {trade_count // 2}"
                )

            time.sleep(0.001)

        elapsed = time.perf_counter() - start_time
        throughput = total_orders / elapsed

        # Each trade contributes latency for its buy and sell order.
        latencies_us = [trade[4] for trade in processed_trades]

        print("\n===== CYTHON BENCHMARK =====")
        print(f"Orders submitted: {total_orders}")
        print(f"Trades executed: {trade_count // 2}")
        print(f"Elapsed time: {elapsed:.6f} seconds")
        print(f"Throughput: {throughput:.2f} orders/second")
        print(f"Measured matched-order latencies: {len(latencies_us)}")
        print(f"Average latency: {statistics.mean(latencies_us):.2f} us")
        print(f"p50 latency: {percentile(latencies_us, 50):.2f} us")
        print(f"p95 latency: {percentile(latencies_us, 95):.2f} us")
        print(f"p99 latency: {percentile(latencies_us, 99):.2f} us")
        print(
            "Note: Latency is measured from order submission to trade "
            "callback; it includes queueing and polling delays."
        )

    finally:
        shutdown[0] = True
        engine_thread.join(timeout=2)
        buffer.close()


if __name__ == "__main__":
    main()
