
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

        # SELL 3 shares at price 100.
        buffer.write_order(9001, 100.0, 3, b"S")

        # BUY 2 shares at price 100.
        buffer.write_order(9002, 100.0, 2, b"B")

        # Wait up to 2 seconds for the expected trade.
        deadline = time.monotonic() + 2

        while time.monotonic() < deadline:
            with trade_lock:
                if trades:
                    break
            time.sleep(0.005)

        with trade_lock:
            actual_trades = list(trades)

        expected = [(9002, 9001, 100.0, 2)]

        assert actual_trades == expected, (
            f"Expected trade {expected}, got {actual_trades}"
        )

        print("PASS: Trade callback verified.")
        print(f"Verified trade: {actual_trades[0]}")

    finally:
        shutdown[0] = True

        if engine_thread is not None:
            engine_thread.join(timeout=2)

        buffer.close()


if __name__ == "__main__":
    main()
