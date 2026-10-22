
from importlib import import_module
from importlib.machinery import EXTENSION_SUFFIXES
from pathlib import Path
import threading
import time

from shared_memory.buffer import SharedMemoryBuffer
import matching_engine
from ui_persistence.ledger import TradeLedger


project_root = Path(__file__).resolve().parent
installed_engine = project_root / "matching_engine"
built_engines = [
    path
    for path in (project_root / "build").glob(
        "lib.*/matching_engine/engine*"
    )
    if any(path.name.endswith(suffix) for suffix in EXTENSION_SUFFIXES)
]

if built_engines:
    latest_built_engine = max(built_engines, key=lambda path: path.stat().st_mtime)
    installed_engines = [
        installed_engine / f"engine{suffix}"
        for suffix in EXTENSION_SUFFIXES
        if (installed_engine / f"engine{suffix}").is_file()
    ]

    if (
        not installed_engines
        or latest_built_engine.stat().st_mtime
        > max(path.stat().st_mtime for path in installed_engines)
    ):
        matching_engine.__path__.insert(0, str(latest_built_engine.parent))

match_order_stream = import_module("matching_engine.engine").match_order_stream


def main():
    buffer = SharedMemoryBuffer()
    ledger = TradeLedger()
    shutdown = [False]

    def save_trade(buy_id, sell_id, price, quantity):
        ledger.record_trade(
            buy_order_id=buy_id,
            sell_order_id=sell_id,
            price=price,
            quantity=quantity
        )
        print("Trade saved to SQLite database.")

    engine_thread = threading.Thread(
        target=match_order_stream,
        args=(buffer, shutdown, save_trade),
        daemon=True
    )

    try:
        engine_thread.start()
        print("Engine is running. Press Ctrl+C to stop.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping engine...")

    finally:
        shutdown[0] = True
        engine_thread.join(timeout=2)
        buffer.close()
        print("Engine stopped.")


if __name__ == "__main__":
    main()
