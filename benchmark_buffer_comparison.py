import statistics
import time

from shared_memory.buffer import SharedMemoryBuffer
from shared_memory.buffer_sharedmemory_experiment import (
    SharedMemoryBufferExperiment
)


OPERATIONS = 20000
REPEATS = 5


def benchmark(buffer_class, label):
    times = []

    for run in range(REPEATS):
        buffer = buffer_class()

        try:
            start = time.perf_counter()

            for i in range(OPERATIONS):
                buffer.write_order(i + 1, 100.0, 1, b"B")
                buffer.read_next_order()

            elapsed = time.perf_counter() - start
            times.append(elapsed)
            print(f"{label} run {run + 1}: {elapsed:.4f} seconds")
        finally:
            buffer.close(unlink=True) if isinstance(
                buffer, SharedMemoryBufferExperiment
            ) else buffer.close()

    median_time = statistics.median(times)
    print(f"{label} median: {median_time:.4f} seconds")
    return median_time


if __name__ == "__main__":
    print(f"Operations per run: {OPERATIONS * 2:,}")
    print()

    original = benchmark(SharedMemoryBuffer, "Original mmap")
    print()
    experimental = benchmark(
        SharedMemoryBufferExperiment, "Experimental shared_memory"
    )

    improvement = (original - experimental) / original * 100

    print("\n===== COMPARISON =====")
    print(f"Original median:     {original:.4f} seconds")
    print(f"Experimental median: {experimental:.4f} seconds")
    print(f"Time reduction:      {improvement:.2f}%")
