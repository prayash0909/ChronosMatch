import multiprocessing as mp
import time

from shared_memory.buffer_experiment import SharedMemoryBuffer

TOTAL_ORDERS = 1_000_000
PROCESS_TIMEOUT = 300
CONSUMER_TIMEOUT = 280


def get_payload(order_id):
    price = 100.0 + (order_id % 1000) / 100.0
    qty = (order_id % 10) + 1
    side = b"B" if order_id % 2 == 0 else b"S"
    return price, qty, side


def producer(ready, reading, done, buffer_lock, result_queue):
    buffer = SharedMemoryBuffer()

    try:
        if not ready.wait(timeout=20):
            raise TimeoutError("Consumer did not become ready")

        if not reading.wait(timeout=20):
            raise TimeoutError("Consumer did not start reading")

        start = time.perf_counter()

        for order_id in range(1, TOTAL_ORDERS + 1):
            price, qty, side = get_payload(order_id)

            while True:
                try:
                    with buffer_lock:
                        buffer.write_order(order_id, price, qty, side)
                    break
                except BufferError:
                    time.sleep(0.0001)

        elapsed = time.perf_counter() - start

        result_queue.put((
            "PRODUCER_DONE",
            TOTAL_ORDERS,
            elapsed
        ))

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
    overlap = False
    expected_id = 1
    deadline = time.monotonic() + CONSUMER_TIMEOUT

    try:
        ready.set()
        reading.set()

        while received < TOTAL_ORDERS:
            with buffer_lock:
                order = buffer.read_next_order()

            if order is None:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Consumer received only {received} orders"
                    )
                time.sleep(0.0001)
                continue

            order_id, price, qty, side = order

            if order_id != expected_id:
                raise ValueError(
                    f"FIFO mismatch: expected {expected_id}, got {order_id}"
                )

            expected_price, expected_qty, expected_side = get_payload(
                order_id
            )

            if (
                price != expected_price
                or qty != expected_qty
                or side != expected_side
            ):
                raise ValueError(
                    f"Invalid payload for order {order_id}"
                )

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


def main():
    mp.freeze_support()

    buffer = SharedMemoryBuffer()
    buffer.reset_buffer()

    ready = mp.Event()
    reading = mp.Event()
    done = mp.Event()
    buffer_lock = mp.Lock()
    result_queue = mp.Queue()

    processes = [
        mp.Process(
            target=consumer,
            args=(ready, reading, done, buffer_lock, result_queue)
        ),
        mp.Process(
            target=producer,
            args=(ready, reading, done, buffer_lock, result_queue)
        ),
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

        results = []

        for _ in range(2):
            try:
                results.append(result_queue.get(timeout=10))
            except Exception:
                break

        total_elapsed = time.perf_counter() - start

        for result in results:
            print(result)

        expected_checksum = (
            TOTAL_ORDERS * (TOTAL_ORDERS + 1) // 2
        )

        producer_ok = any(
            r[0] == "PRODUCER_DONE" and r[1] == TOTAL_ORDERS
            for r in results
        )

        consumer_ok = any(
            r[0] == "CONSUMER_DONE"
            and r[1] == TOTAL_ORDERS
            and r[2] == expected_checksum
            and r[3] is True
            for r in results
        )

        process_ok = all(p.exitcode == 0 for p in processes)

        if producer_ok and consumer_ok and process_ok:
            print("\nPASS: 1,000,000 orders verified.")
            print("FIFO: PASS")
            print("Payload validation: PASS")
            print("Checksum: PASS")
            print("Producer-consumer overlap: PASS")
            print(f"Total elapsed: {total_elapsed:.3f} seconds")
            print(
                f"End-to-end throughput: "
                f"{TOTAL_ORDERS / total_elapsed:,.0f} orders/second"
            )
        else:
            print("\nFAIL: Million-order audit did not pass.")
            print("Process exit codes:", [p.exitcode for p in processes])

    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)

        buffer.close()
        result_queue.close()
        result_queue.join_thread()


if __name__ == "__main__":
    main()
