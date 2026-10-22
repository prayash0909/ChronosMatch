
import threading
import time

from shared_memory.buffer import SharedMemoryBuffer
from matching_engine.engine import match_order_stream


def main():
    buffer = SharedMemoryBuffer()
    buffer.reset_buffer()

    shutdown = [False]
    trades = []
    trade_lock = threading.Lock()
    engine_thread = None

    def on_trade(buy_id, sell_id, price, quantity):
        with trade_lock:
            trades.append((buy_id, sell_id, price, quantity))

    try:
        engine_thread = threading.Thread(
            target=match_order_stream,
            args=(buffer, shutdown, on_trade),
            kwargs={"verbose": False},
            daemon=True
        )
        engine_thread.start()
        time.sleep(0.1)

        # First SELL has a worse price.
        buffer.write_order(9101, 101.0, 2, b"S")

        # These SELL orders have the same, better price.
        buffer.write_order(9102, 100.0, 2, b"S")
        buffer.write_order(9103, 100.0, 3, b"S")

        # BUY should match the best-priced SELL orders first,
        # and preserve FIFO for orders at the same price.
        buffer.write_order(9104, 101.0, 3, b"B")

        deadline = time.monotonic() + 3

        while time.monotonic() < deadline:
            with trade_lock:
                if sum(t[3] for t in trades) >= 3:
                    break
            time.sleep(0.005)

        with trade_lock:
            actual_trades = list(trades)

        expected_trades = [
            (9104, 9102, 100.0, 2),
            (9104, 9103, 100.0, 1),
        ]

        assert actual_trades == expected_trades, (
            f"\nExpected: {expected_trades}"
            f"\nActual:   {actual_trades}"
        )

        print("PASS: Price-Time Priority verified.")
        for trade in actual_trades:
            print(f"Verified trade: {trade}")

    finally:
        shutdown[0] = True

        if engine_thread is not None:
            engine_thread.join(timeout=2)

        buffer.close()


if __name__ == "__main__":
    main()
