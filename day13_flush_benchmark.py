import statistics
import time

from shared_memory.buffer import SharedMemoryBuffer as FlushBuffer
from shared_memory.buffer_experiment import SharedMemoryBuffer as NoFlushBuffer

ITERATIONS = 20_000
REPEATS = 5


def run_test(buffer_class):
    results = []

    for run in range(REPEATS):
        buffer = buffer_class()
        buffer.reset_buffer()

        start = time.perf_counter()

        try:
            for i in range(ITERATIONS):
                order_id = i + 1

                buffer.write_order(order_id, 100.0, 1, b"B")
                order = buffer.read_next_order()

                expected = (order_id, 100.0, 1, b"B")

                if order != expected:
                    raise ValueError(
                        f"Data mismatch: expected {expected}, got {order}"
                    )

            elapsed = time.perf_counter() - start
            results.append(elapsed)

            print(f"Run {run + 1}: {elapsed:.4f} seconds")

        finally:
            buffer.close()

    return statistics.median(results)


def main():
    print("\n========== WITH FLUSH ==========")
    flush_median = run_test(FlushBuffer)

    print("\n========== WITHOUT FLUSH ==========")
    no_flush_median = run_test(NoFlushBuffer)

    print("\n========== FLUSH COMPARISON ==========")
    print(f"With flush median:    {flush_median:.4f} seconds")
    print(f"Without flush median: {no_flush_median:.4f} seconds")

    if flush_median > no_flush_median:
        improvement = (
            (flush_median - no_flush_median) / flush_median
        ) * 100

        print(f"Time reduction without flush: {improvement:.2f}%")
    else:
        print("No-flush mode did not improve median execution time.")

    print("\nAll data integrity checks passed.")


if __name__ == "__main__":
    main()
