import statistics
import time

from shared_memory.buffer import SharedMemoryBuffer as OriginalBuffer
from shared_memory.buffer_experiment import SharedMemoryBuffer as ExperimentalBuffer

ITERATIONS = 20000
REPEATS = 5


def run_once(buffer_class):
    buffer = buffer_class()

    try:
        buffer.reset_buffer()
        start = time.perf_counter()

        for i in range(ITERATIONS):
            expected_id = i + 1
            buffer.write_order(expected_id, 100.0, 1, b"B")
            order = buffer.read_next_order()

            if order is None:
                raise AssertionError(f"Missing order {expected_id}")

            order_id, price, qty, side = order

            if (order_id, price, qty, side) != (expected_id, 100.0, 1, b"B"):
                raise AssertionError(
                    f"Incorrect order: expected ID {expected_id}, got {order}"
                )

        return time.perf_counter() - start

    finally:
        buffer.close()


def main():
    results = {
        "Original mmap": [],
        "Experimental mmap": [],
    }

    for run in range(REPEATS):
        implementations = [
            ("Original mmap", OriginalBuffer),
            ("Experimental mmap", ExperimentalBuffer),
        ]

        if run % 2 == 1:
            implementations.reverse()

        for name, buffer_class in implementations:
            elapsed = run_once(buffer_class)
            results[name].append(elapsed)
            print(f"Run {run + 1} - {name}: {elapsed:.4f} seconds")

    original_median = statistics.median(results["Original mmap"])
    experimental_median = statistics.median(results["Experimental mmap"])
    improvement = (
        (original_median - experimental_median) / original_median
    ) * 100

    print("\n--- Final Comparison ---")
    print(f"Original median:     {original_median:.4f} seconds")
    print(f"Experimental median: {experimental_median:.4f} seconds")
    print(f"Experimental improvement: {improvement:.2f}%")
    print("PASS: All orders verified in every run.")


if __name__ == "__main__":
    main()
