import multiprocessing as mp
import time

from shared_memory.buffer_sharedmemory_experiment import (
    SharedMemoryBufferExperiment
)

TOTAL_ORDERS = 5000


def producer(shm_name, result_queue):
    buffer = SharedMemoryBufferExperiment(
        name=shm_name,
        create=False
    )

    try:
        for order_id in range(1, TOTAL_ORDERS + 1):
            while True:
                try:
                    buffer.write_order(
                        order_id, 100.0, 1, b"B"
                    )
                    break
                except BufferError:
                    time.sleep(0.0001)

        result_queue.put(("producer_done", TOTAL_ORDERS))
    except Exception as exc:
        result_queue.put(("producer_error", repr(exc)))
    finally:
        buffer.close()


def consumer(shm_name, result_queue):
    buffer = SharedMemoryBufferExperiment(
        name=shm_name,
        create=False
    )

    received = 0
    expected_id = 1

    try:
        deadline = time.monotonic() + 30

        while received < TOTAL_ORDERS:
            order = buffer.read_next_order()

            if order is None:
                if time.monotonic() > deadline:
                    result_queue.put(
                        ("consumer_timeout", received)
                    )
                    return
                time.sleep(0.0001)
                continue

            order_id, price, qty, side = order

            if order_id != expected_id:
                result_queue.put(
                    ("consumer_error",
                     f"Expected {expected_id}, got {order_id}")
                )
                return

            if price != 100.0 or qty != 1 or side != b"B":
                result_queue.put(
                    ("consumer_error", f"Invalid order: {order}")
                )
                return

            received += 1
            expected_id += 1

        result_queue.put(("consumer_done", received))
    except Exception as exc:
        result_queue.put(("consumer_error", repr(exc)))
    finally:
        buffer.close()


def main():
    mp.freeze_support()

    owner = SharedMemoryBufferExperiment(create=True)
    result_queue = mp.Queue()

    print("Shared memory name:", owner.name)
    print("Starting producer and consumer...")

    processes = [
        mp.Process(target=consumer, args=(owner.name, result_queue)),
        mp.Process(target=producer, args=(owner.name, result_queue)),
    ]

    try:
        for process in processes:
            process.start()

        for process in processes:
            process.join(35)

        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join()

        results = []
        while not result_queue.empty():
            results.append(result_queue.get())

        for result in results:
            print(result)

        if (
            all(p.exitcode == 0 for p in processes)
            and ("consumer_done", TOTAL_ORDERS) in results
            and ("producer_done", TOTAL_ORDERS) in results
        ):
            print(f"PASS: All {TOTAL_ORDERS} orders transferred in order.")
        else:
            print("FAIL: Multiprocess queue test did not complete successfully.")

    finally:
        result_queue.close()
        owner.close(unlink=True)


if __name__ == "__main__":
    main()
