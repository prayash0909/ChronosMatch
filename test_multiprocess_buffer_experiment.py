
import multiprocessing as mp
import time

from shared_memory.buffer_experiment import SharedMemoryBuffer

TOTAL_ORDERS = 5000


def producer():
    print("Producer: starting", flush=True)
    buffer = SharedMemoryBuffer()

    try:
        print("Producer: buffer opened", flush=True)

        for i in range(TOTAL_ORDERS):
            while True:
                try:
                    buffer.write_order(i + 1, 100.0, 1, b"B")
                    break
                except BufferError:
                    time.sleep(0.0005)

        print("Producer: all orders written", flush=True)

    except Exception as exc:
        print(f"Producer ERROR: {exc!r}", flush=True)
        raise
    finally:
        buffer.close()


def consumer(result_queue):
    print("Consumer: starting", flush=True)
    buffer = SharedMemoryBuffer()
    received_ids = []

    try:
        print("Consumer: buffer opened", flush=True)
        deadline = time.monotonic() + 30

        while len(received_ids) < TOTAL_ORDERS:
            order = buffer.read_next_order()

            if order is not None:
                received_ids.append(order[0])
            elif time.monotonic() > deadline:
                result_queue.put(("TIMEOUT", len(received_ids)))
                print(
                    f"Consumer: timeout at {len(received_ids)} orders",
                    flush=True
                )
                return
            else:
                time.sleep(0.0005)

        result_queue.put(("OK", received_ids))
        print("Consumer: all orders received", flush=True)

    except Exception as exc:
        print(f"Consumer ERROR: {exc!r}", flush=True)
        result_queue.put(("ERROR", repr(exc)))
        raise
    finally:
        buffer.close()



def main():
    # Run only one consumer and one producer.
    buffer = SharedMemoryBuffer()
    buffer.reset_buffer()
    buffer.close()

    result_queue = mp.Queue()

    consumer_process = mp.Process(
        target=consumer,
        args=(result_queue,)
    )
    producer_process = mp.Process(target=producer)

    consumer_process.start()
    producer_process.start()

    producer_process.join(timeout=35)
    consumer_process.join(timeout=35)

    if producer_process.is_alive():
        producer_process.terminate()
        producer_process.join()

    if consumer_process.is_alive():
        consumer_process.terminate()
        consumer_process.join()

    if producer_process.exitcode != 0:
        print("FAIL: Producer process did not finish correctly.")
    elif consumer_process.exitcode != 0:
        print("FAIL: Consumer process did not finish correctly.")
    elif not result_queue.empty():
        status, result = result_queue.get()

        if status == "OK":
            expected = list(range(1, TOTAL_ORDERS + 1))

            if result == expected:
                print("PASS: Multiprocess FIFO stress test.")
                print(f"Orders verified: {len(result)}")
                print("Order IDs are correct and sequential.")
            else:
                print("FAIL: Order mismatch detected.")
                print(f"Orders received: {len(result)}")
        else:
            print(f"FAIL: Consumer timeout. Orders received: {result}")
    else:
        print("FAIL: No result received from consumer.")


if __name__ == "__main__":
    mp.freeze_support()
    main()
