
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

        # SELL only 2 units.
        buffer.write_order(9201, 100.0, 2, b"S")

        # BUY requests 5 units.
        buffer.write_order(9202, 100.0, 5, b"B")

        deadline = time.monotonic() + 3

        while time.monotonic() < deadline:
            with lock:
                if trades:
                    break
            time.sleep(0.005)

        with lock:
            actual_trades = list(trades)

        expected = [(9202, 9201, 100.0, 2)]

        assert actual_trades == expected, (
            f"Expected {expected}, got {actual_trades}"
        )

        print("PASS: Partial fill trade verified.")
        print(f"Verified trade: {actual_trades[0]}")
        print("Expected remaining BUY quantity: 3")

    finally:
        shutdown[0] = True

        if engine_thread is not None:
            engine_thread.join(timeout=2)

        buffer.close()


if __name__ == "__main__":
    main()
