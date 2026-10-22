
import threading
import time

from shared_memory.buffer import SharedMemoryBuffer
from matching_engine.engine import match_order_stream


def main():
    buffer = SharedMemoryBuffer()
    buffer.reset_buffer()

    shutdown = [False]
    trades = []
    lock = threading.Lock()
    engine_thread = None

    def on_trade(buy_id, sell_id, price, quantity):
        with lock:
            trades.append((buy_id, sell_id, price, quantity))

    try:
        engine_thread = threading.Thread(
            target=match_order_stream,
            args=(buffer, shutdown, on_trade),
            kwargs={"verbose": False},
            daemon=True,
        )
        engine_thread.start()
        time.sleep(0.1)

        # Invalid quantity and side should be ignored.
        buffer.write_order(9301, 100.0, 0, b"S")
        buffer.write_order(9302, 100.0, -5, b"B")
        buffer.write_order(9303, 100.0, 2, b"B")

        # A valid SELL should match only the valid BUY.
        buffer.write_order(9304, 100.0, 2, b"S")

        deadline = time.monotonic() + 3

        while time.monotonic() < deadline:
            with lock:
                if trades:
                    break
            time.sleep(0.005)

        with lock:
            actual_trades = list(trades)

        expected = [(9303, 9304, 100.0, 2)]

        assert actual_trades == expected, (
            f"Expected {expected}, got {actual_trades}"
        )

        print("PASS: Invalid quantities ignored.")
        print(f"Verified trade: {actual_trades[0]}")

    finally:
        shutdown[0] = True

        if engine_thread is not None:
            engine_thread.join(timeout=2)

        buffer.close()


if __name__ == "__main__":
    main()
