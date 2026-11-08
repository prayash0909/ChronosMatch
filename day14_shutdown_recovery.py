import multiprocessing as mp
import os

from shared_memory.buffer_experiment import SharedMemoryBuffer


PRODUCER_TAG = "Local\\ChronosMatchDay14ProducerCrash"
CONSUMER_TAG = "Local\\ChronosMatchDay14ConsumerCrash"


def producer_crash_worker(tag):
    buffer = SharedMemoryBuffer(tag_name=tag)

    for order_id in range(1, 4):
        buffer.write_order(order_id, float(order_id), 1, b"B")

    # Simulate unexpected process termination.
    os._exit(0)


def consumer_crash_worker(tag):
    buffer = SharedMemoryBuffer(tag_name=tag)

    for expected_id in range(1, 3):
        order = buffer.read_next_order()

        if order is None or order[0] != expected_id:
            os._exit(2)

    # Simulate unexpected process termination.
    os._exit(0)


def run_process(worker, tag):
    process = mp.Process(target=worker, args=(tag,))
    process.start()
    process.join(timeout=20)

    if process.is_alive():
        process.terminate()
        process.join(timeout=5)
        raise TimeoutError("Child process did not shut down")

    if process.exitcode != 0:
        raise RuntimeError(
            f"Child process failed with exit code {process.exitcode}"
        )


def test_producer_crash():
    buffer = SharedMemoryBuffer(tag_name=PRODUCER_TAG)
    buffer.reset_buffer()

    try:
        run_process(producer_crash_worker, PRODUCER_TAG)

        received = []

        while True:
            order = buffer.read_next_order()
            if order is None:
                break
            received.append(order[0])

        assert received == [1, 2, 3], received

        print("PASS: Producer crash recovery.")
        print("Orders recovered:", received)

    finally:
        buffer.reset_buffer()
        buffer.close()


def test_consumer_crash():
    buffer = SharedMemoryBuffer(tag_name=CONSUMER_TAG)
    buffer.reset_buffer()

    try:
        for order_id in range(1, 5):
            buffer.write_order(
                order_id,
                float(order_id),
                1,
                b"B"
            )

        run_process(consumer_crash_worker, CONSUMER_TAG)

        remaining = []

        while True:
            order = buffer.read_next_order()
            if order is None:
                break
            remaining.append(order[0])

        assert remaining == [3, 4], remaining

        print("PASS: Consumer crash recovery.")
        print("Remaining orders:", remaining)

    finally:
        buffer.reset_buffer()
        buffer.close()


def test_stale_data_reset():
    buffer = SharedMemoryBuffer(tag_name=PRODUCER_TAG)

    try:
        buffer.reset_buffer()

        for order_id in range(1, 4):
            buffer.write_order(order_id, 100.0, 1, b"B")

        buffer.reset_buffer()

        assert buffer.read_next_order() is None

        write_seq, read_seq = __import__("struct").unpack(
            "<QQ",
            buffer.mm[8:24]
        )

        assert write_seq == 0
        assert read_seq == 0

        print("PASS: Stale data reset.")
        print(f"Reset counters: write={write_seq}, read={read_seq}")

    finally:
        buffer.reset_buffer()
        buffer.close()


def main():
    test_producer_crash()
    test_consumer_crash()
    test_stale_data_reset()

    print("\nPASS: All shutdown and recovery tests completed.")


if __name__ == "__main__":
    mp.freeze_support()
    main()
