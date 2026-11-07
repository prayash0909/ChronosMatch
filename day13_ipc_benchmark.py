import multiprocessing as mp
import statistics
import time
from contextlib import nullcontext

from shared_memory.buffer_experiment import SharedMemoryBuffer

TOTAL_ORDERS = 300_000
REPEATS = 3
PROCESS_TIMEOUT = 120
POLL_INTERVAL = 0.0001


def get_payload(order_id):
    price = 100.0 + (order_id % 1000) / 100.0
    qty = (order_id % 10) + 1
    side = b"B" if order_id % 2 == 0 else b"S"
    return price, qty, side


def lock_context(buffer_lock):
    return buffer_lock if buffer_lock is not None else nullcontext()


def producer(ready, reading, done, buffer_lock, result_queue):
    buffer = SharedMemoryBuffer()

    try:
        if not ready.wait(timeout=20):
            raise TimeoutError("Consumer not ready")

        if not reading.wait(timeout=20):
            raise TimeoutError("Consumer not reading")

        start = time.perf_counter()

        for order_id in range(1, TOTAL_ORDERS + 1):
            price, qty, side = get_payload(order_id)

            while True:
                try:
                    with lock_context(buffer_lock):
                        buffer.write_order(order_id, price, qty, side)
                    break
                except BufferError:
                    time.sleep(POLL_INTERVAL)

        elapsed = time.perf_counter() - start
        result_queue.put(("PRODUCER_DONE", elapsed))

    except Exception as exc:
        result_queue.put(("PRODUCER_ERROR", repr(exc)))
        raise

    finally:
        done.set()
        buffer.close()


def consumer(ready, reading, done, buffer_lock, result_queue):
    buffer = SharedMemoryBuffer()

    received = 0
    checksum = 0
    expected_id = 1
    overlap = False
    deadline = time.monotonic() + PROCESS_TIMEOUT - 10

    try:
        ready.set()
        reading.set()

        while received < TOTAL_ORDERS:
            with lock_context(buffer_lock):
                order = buffer.read_next_order()

            if order is None:
                if time.monotonic() > deadline:
                    raise TimeoutError(
                        f"Received only {received} orders"
                    )
                time.sleep(POLL_INTERVAL)
                continue

            order_id, price, qty, side = order

            if order_id != expected_id:
                raise ValueError(
                    f"FIFO error: expected {expected_id}, got {order_id}"
                )

            expected = get_payload(order_id)

            if (price, qty, side) != expected:
                raise ValueError(f"Payload error at order {order_id}")

            received += 1
            checksum += order_id
            expected_id += 1

            if not done.is_set():
                overlap = True

        result_queue.put((
            "CONSUMER_DONE",
            received,
            checksum,
            overlap
        ))

    except Exception as exc:
        result_queue.put(("CONSUMER_ERROR", repr(exc)))
        raise

    finally:
        buffer.close()


def run_once(use_lock):
    buffer = SharedMemoryBuffer()
    buffer.reset_buffer()

    ready = mp.Event()
    reading = mp.Event()
    done = mp.Event()
    buffer_lock = mp.Lock() if use_lock else None
    result_queue = mp.Queue()

    processes = [
        mp.Process(
            target=consumer,
            args=(ready, reading, done, buffer_lock, result_queue)
        ),
        mp.Process(
            target=producer,
            args=(ready, reading, done, buffer_lock, result_queue)
        )
    ]

    start = time.perf_counter()

    try:
        for process in processes:
            process.start()

        for process in processes:
            process.join(timeout=PROCESS_TIMEOUT)

        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)

        elapsed = time.perf_counter() - start

        results = []
        for _ in range(2):
            try:
                results.append(result_queue.get(timeout=5))
            except Exception:
                break

        expected_checksum = TOTAL_ORDERS * (TOTAL_ORDERS + 1) // 2

        producer_result = next(
            (r for r in results if r[0] == "PRODUCER_DONE"),
            None
        )
        consumer_result = next(
            (r for r in results if r[0] == "CONSUMER_DONE"),
            None
        )

        errors = [r for r in results if r[0].endswith("ERROR")]
        process_ok = all(p.exitcode == 0 for p in processes)

        valid = (
            producer_result is not None
            and consumer_result is not None
            and consumer_result[1] == TOTAL_ORDERS
            and consumer_result[2] == expected_checksum
            and consumer_result[3] is True
            and process_ok
            and not errors
        )

        return {
            "valid": valid,
            "elapsed": elapsed,
            "producer_time": (
                producer_result[1] if producer_result else None
            ),
            "throughput": TOTAL_ORDERS / elapsed if valid else 0,
            "errors": errors,
            "exitcodes": [p.exitcode for p in processes]
        }

    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)

        buffer.close()
        result_queue.close()
        result_queue.join_thread()


def main():
    mp.freeze_support()

    all_results = {}

    for mode, use_lock in [("LOCK", True), ("NO_LOCK", False)]:
        print(f"\n========== {mode} ==========")
        run_results = []

        for run in range(1, REPEATS + 1):
            result = run_once(use_lock)

            if not result["valid"]:
                print(f"Run {run}: FAIL")
                print("Errors:", result["errors"])
                print("Exit codes:", result["exitcodes"])
                raise RuntimeError(f"{mode} benchmark failed")

            run_results.append(result["throughput"])

            print(
                f"Run {run}: {result['elapsed']:.3f}s | "
                f"{result['throughput']:,.0f} orders/sec | "
                f"FIFO: PASS | Payload: PASS | Checksum: PASS"
            )

        median = statistics.median(run_results)
        all_results[mode] = median
        print(f"{mode} median: {median:,.0f} orders/sec")

    no_lock = all_results["NO_LOCK"]
    locked = all_results["LOCK"]

    print("\n========== COMPARISON ==========")
    print(f"No-lock median: {no_lock:,.0f} orders/sec")
    print(f"Lock median:    {locked:,.0f} orders/sec")

    if no_lock > locked:
        improvement = (no_lock / locked - 1) * 100
        print(f"No-lock is {improvement:.2f}% faster.")
    elif locked > no_lock:
        improvement = (locked / no_lock - 1) * 100
        print(f"Lock mode is {improvement:.2f}% faster.")
    else:
        print("Both modes have equal median throughput.")

    print("\nAll benchmark runs passed validation.")


if __name__ == "__main__":
    main()
