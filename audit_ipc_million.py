"""Multiprocess mmap IPC audit.

Run with: python audit_ipc_million.py --orders 1000000
This is a correctness/stress audit, not a claim that one million orders/s is reached.
"""
import argparse
import multiprocessing as mp
import queue
import time
import uuid

from shared_memory.buffer import SharedMemoryBuffer


def _producer(tag_name, count, ready, result):
    buffer = SharedMemoryBuffer(tag_name=tag_name)
    try:
        ready.wait()
        sent = 0
        order_id = 1
        while sent < count:
            try:
                buffer.write_order(order_id, 100.0 + (order_id % 20) / 100, 1, b"B" if order_id % 2 else b"S")
                sent += 1
                order_id += 1
            except BufferError:
                time.sleep(0)
        result.put(("producer", sent, None))
    except Exception as exc:
        result.put(("producer", 0, repr(exc)))
    finally:
        buffer.close()


def _consumer(tag_name, count, ready, result):
    buffer = SharedMemoryBuffer(tag_name=tag_name)
    try:
        ready.wait()
        received = 0
        last_id = 0
        while received < count:
            item = buffer.read_next_order()
            if item is None:
                time.sleep(0)
                continue
            order_id, price, qty, side = item
            if order_id != last_id + 1:
                raise AssertionError(f"sequence mismatch: expected {last_id + 1}, got {order_id}")
            if qty != 1 or side not in (b"B", b"S"):
                raise AssertionError(f"invalid order payload: {item!r}")
            last_id = order_id
            received += 1
        result.put(("consumer", received, None))
    except Exception as exc:
        result.put(("consumer", 0, repr(exc)))
    finally:
        buffer.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orders", type=int, default=1_000_000)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    if args.orders < 1 or args.timeout < 1:
        parser.error("--orders and --timeout must be positive")

    # A unique tag prevents stale state from a prior run contaminating this audit.
    tag_name = "Local\\ChronosAudit" + uuid.uuid4().hex[:16]
    # Default queue is 2 MiB; consumer drains continuously while producer writes.
    ready = mp.Event()
    result = mp.Queue()
    producer = mp.Process(target=_producer, args=(tag_name, args.orders, ready, result))
    consumer = mp.Process(target=_consumer, args=(tag_name, args.orders, ready, result))
    # Initialize/reset the named mapping once before either child attaches.
    owner = SharedMemoryBuffer(tag_name=tag_name)
    owner.reset_buffer()
    producer.start()
    consumer.start()
    started = time.perf_counter()
    ready.set()
    producer.join(args.timeout)
    consumer.join(args.timeout)
    elapsed = time.perf_counter() - started
    if producer.is_alive():
        producer.terminate()
    if consumer.is_alive():
        consumer.terminate()
    producer.join()
    consumer.join()
    owner.close()

    results = []
    for _ in range(2):
        try:
            results.append(result.get(timeout=2))
        except queue.Empty:
            break
    errors = [row for row in results if row[2] is not None]
    counts = {row[0]: row[1] for row in results}
    print(f"IPC audit requested={args.orders:,} elapsed={elapsed:.3f}s")
    print(f"producer={counts.get('producer', 0):,} consumer={counts.get('consumer', 0):,} throughput={counts.get('consumer', 0) / elapsed if elapsed else 0:,.0f} orders/s")
    if errors or producer.exitcode != 0 or consumer.exitcode != 0 or counts.get("producer") != args.orders or counts.get("consumer") != args.orders:
        print("FAIL", errors, "exitcodes", producer.exitcode, consumer.exitcode)
        raise SystemExit(1)
    print("PASS: all orders crossed the shared-memory IPC queue in sequence")


if __name__ == "__main__":
    mp.freeze_support()
    main()
