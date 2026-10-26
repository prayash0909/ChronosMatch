
import multiprocessing as mp
import struct
import time

from shared_memory.buffer_experiment import SharedMemoryBuffer

TOTAL_ORDERS = 5000
BATCH_SIZE = 100
PROCESS_TIMEOUT_SECONDS = 35
CONSUMER_TIMEOUT_SECONDS = 30
RETRY_DELAY_SECONDS = 0.0005
BATCH_DELAY_SECONDS = 0.001


def producer(consumer_ready, consumer_reading, producer_done):
    """Write sequential order IDs while the consumer is ready to read."""
    print("Producer: starting", flush=True)
    buffer = SharedMemoryBuffer()

    try:
        print("Producer: buffer opened", flush=True)

        if not consumer_ready.wait(timeout=10):
            raise TimeoutError("Consumer did not become ready")

        if not consumer_reading.wait(timeout=10):
            raise TimeoutError("Consumer did not start reading")

        print("Producer: consumer is reading; starting writes", flush=True)

        for batch_start in range(0, TOTAL_ORDERS, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, TOTAL_ORDERS)

            for i in range(batch_start, batch_end):
                order_id = i + 1

                while True:
                    try:
                        buffer.write_order(order_id, 100.0, 1, b"B")
                        break
                    except BufferError:
                        time.sleep(RETRY_DELAY_SECONDS)

            # Give the consumer a chance to read between batches.
            time.sleep(BATCH_DELAY_SECONDS)

        print(
            "Producer final counters:",
            struct.unpack("<QQ", buffer.mm[8:24]),
            flush=True,
        )
        print("Producer: all orders written", flush=True)

    except Exception as exc:
        print(f"Producer ERROR: {exc!r}", flush=True)
        raise
    finally:
        producer_done.set()
        buffer.close()


def consumer(
    result_queue,
    consumer_ready,
    consumer_reading,
    producer_done,
):
    """Verify FIFO order and detect reads before production completes."""
    print("Consumer: starting", flush=True)
    buffer = SharedMemoryBuffer()
    received_ids = []
    overlap_observed = False

    try:
        print("Consumer: buffer opened", flush=True)
        consumer_ready.set()

        deadline = time.monotonic() + CONSUMER_TIMEOUT_SECONDS

        # Signal before the first read so the producer can start writing.
        consumer_reading.set()

        while len(received_ids) < TOTAL_ORDERS:
            order = buffer.read_next_order()

            if order is not None:
                received_ids.append(order[0])

                if not producer_done.is_set():
                    overlap_observed = True

            elif time.monotonic() >= deadline:
                result_queue.put(
                    ("TIMEOUT", len(received_ids), overlap_observed)
                )
                print(
                    f"Consumer: timeout at {len(received_ids)} orders",
                    flush=True,
                )
                return
            else:
                time.sleep(RETRY_DELAY_SECONDS)

        result_queue.put(("OK", received_ids, overlap_observed))
        print("Consumer: all orders received", flush=True)

    except Exception as exc:
        print(f"Consumer ERROR: {exc!r}", flush=True)
        result_queue.put(("ERROR", repr(exc), overlap_observed))
        raise
    finally:
        buffer.close()


def main():
    """Run a synchronized multiprocess FIFO and overlap test."""
    buffer = SharedMemoryBuffer()
    result_queue = mp.Queue()

    consumer_ready = mp.Event()
    consumer_reading = mp.Event()
    producer_done = mp.Event()

    producer_process = None
    consumer_process = None

    try:
        buffer.reset_buffer()

        consumer_process = mp.Process(
            target=consumer,
            args=(
                result_queue,
                consumer_ready,
                consumer_reading,
                producer_done,
            ),
        )

        producer_process = mp.Process(
            target=producer,
            args=(
                consumer_ready,
                consumer_reading,
                producer_done,
            ),
        )

        consumer_process.start()
        producer_process.start()

        producer_process.join(timeout=PROCESS_TIMEOUT_SECONDS)
        consumer_process.join(timeout=PROCESS_TIMEOUT_SECONDS)

        for process in (producer_process, consumer_process):
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)

        if producer_process.exitcode != 0:
            print(
                "FAIL: Producer process exited with code "
                f"{producer_process.exitcode}"
            )
            return

        if consumer_process.exitcode != 0:
            print(
                "FAIL: Consumer process exited with code "
                f"{consumer_process.exitcode}"
            )
            return

        try:
            status, result, overlap_observed = result_queue.get(timeout=2)
        except Exception as exc:
            print(f"FAIL: No consumer result received: {exc!r}")
            return

        if status != "OK":
            print(f"FAIL: Consumer reported {status}: {result}")
            return

        expected_ids = list(range(1, TOTAL_ORDERS + 1))

        if result != expected_ids:
            print("FAIL: FIFO order mismatch.")
            print(f"Expected IDs: {TOTAL_ORDERS}")
            print(f"Received IDs: {len(result)}")
            return

        if not overlap_observed:
            print(
                "FAIL: FIFO passed, but overlapping read/write "
                "activity was not observed."
            )
            return

        print("PASS: Multiprocess FIFO and overlap test.")
        print(f"Orders verified: {len(result)}")
        print("Order IDs are correct and sequential.")
        print("Consumer read orders before producer finished writing.")

    finally:
        for process in (producer_process, consumer_process):
            if process is not None and process.is_alive():
                process.terminate()
                process.join(timeout=5)

        buffer.close()
        result_queue.close()
        result_queue.join_thread()


if __name__ == "__main__":
    mp.freeze_support()
    main()
