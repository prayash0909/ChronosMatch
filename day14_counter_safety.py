import struct

from shared_memory.buffer_experiment import SharedMemoryBuffer


def expect_runtime_error(operation, label):
    try:
        operation()
    except RuntimeError as exc:
        print(f"PASS: {label}: {exc}")
        return

    raise AssertionError(f"FAIL: {label} did not raise RuntimeError")


def main():
    buffer = SharedMemoryBuffer(size=128)
    capacity = buffer.capacity

    try:
        # Case 1: write_seq is smaller than read_seq.
        buffer.reset_buffer()
        buffer.mm[8:24] = struct.pack("<QQ", 0, 1)

        expect_runtime_error(
            lambda: buffer.write_order(1, 100.0, 1, b"B"),
            "write_seq < read_seq (write)"
        )

        expect_runtime_error(
            buffer.read_next_order,
            "write_seq < read_seq (read)"
        )

        # Case 2: Queue difference exceeds capacity.
        buffer.reset_buffer()
        buffer.mm[8:24] = struct.pack("<QQ", capacity + 1, 0)

        expect_runtime_error(
            lambda: buffer.write_order(1, 100.0, 1, b"B"),
            "Queue counters exceed capacity (write)"
        )

        expect_runtime_error(
            buffer.read_next_order,
            "Queue counters exceed capacity (read)"
        )

        print("\nPASS: All counter consistency checks passed.")

    finally:
        buffer.reset_buffer()
        buffer.close()


if __name__ == "__main__":
    main()

