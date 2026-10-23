
from importlib import import_module
from importlib.machinery import EXTENSION_SUFFIXES
from pathlib import Path
import csv
import queue
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
    metrics_path = project_root / "latency_metrics.csv"
    metrics_file = metrics_path.open("a", newline="", encoding="utf-8")
    metrics_writer = csv.DictWriter(metrics_file, fieldnames=["timestamp_ns", "buy_order_id", "sell_order_id", "price", "quantity", "latency_ns"])
    if metrics_path.stat().st_size == 0:
        metrics_writer.writeheader()

    def record_metrics(row):
        metrics_writer.writerow(row)

    trade_queue = queue.Queue()
    stop_worker = object()

    def persist_trades():
        while True:
            item = trade_queue.get()
            try:
                if item is stop_worker:
                    return
                buy_id, sell_id, price, quantity = item
                ledger.record_trade(
                    buy_order_id=buy_id,
                    sell_order_id=sell_id,
                    price=price,
                    quantity=quantity
                )
            except Exception as exc:
                print(f"[LEDGER ERROR] {exc}")
            finally:
                trade_queue.task_done()

    ledger_thread = threading.Thread(target=persist_trades, name="trade-ledger-writer", daemon=True)

    def save_trade(buy_id, sell_id, price, quantity):
        # Keep SQLite I/O off the matching thread; the worker persists in FIFO order.
        trade_queue.put((buy_id, sell_id, price, quantity))

    engine_thread = threading.Thread(
        target=match_order_stream,
        args=(buffer, shutdown, save_trade),
        kwargs={"metrics_callback": record_metrics},
        daemon=True
    )

    try:
        ledger_thread.start()
        engine_thread.start()
        print("Engine is running with background SQLite ledger writer. Press Ctrl+C to stop.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping engine...")

    finally:
        shutdown[0] = True
        engine_thread.join(timeout=2)
        trade_queue.join()
        trade_queue.put(stop_worker)
        ledger_thread.join(timeout=5)
        buffer.close()
        metrics_file.close()
        print(f"Engine stopped. Trade latency metrics: {metrics_path}")


if __name__ == "__main__":
    main()
