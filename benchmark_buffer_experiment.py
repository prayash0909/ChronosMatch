import statistics
import time

from shared_memory.buffer_experiment import SharedMemoryBuffer


def run_test(iterations=20000, repeats=5):
    results = []

    for run in range(repeats):
        buffer = SharedMemoryBuffer()
        buffer.reset_buffer()

        start = time.perf_counter()

        try:
            for i in range(iterations):
                buffer.write_order(i + 1, 100.0, 1, b"B")
                buffer.read_next_order()
        finally:
            elapsed = time.perf_counter() - start
            buffer.close()

        results.append(elapsed)
        print(f"Run {run + 1}: {elapsed:.4f} seconds")

    print(f"\nMedian time: {statistics.median(results):.4f} seconds")
    print(f"Operations: {iterations * 2:,} read/write operations per run")


if __name__ == "__main__":
    run_test()