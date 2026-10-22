
from shared_memory.buffer import SharedMemoryBuffer


def main():
    buffer = SharedMemoryBuffer(size=64)
    buffer.reset_buffer()

    try:
        # Calculate the actual queue capacity.
        capacity = buffer.capacity
        print("Queue capacity:", capacity)

        # Fill the queue completely.
        for i in range(capacity):
            buffer.write_order(9500 + i, 100.0, 1, b"B")

        # The next write must fail because the queue is full.
        try:
            buffer.write_order(9999, 101.0, 1, b"S")
        except BufferError:
            print("PASS: Full queue rejects additional orders.")
        else:
            raise AssertionError("Expected BufferError for full queue")

        # Confirm the first queued order was not overwritten.
        first = buffer.read_next_order()
        expected = (9500, 100.0, 1, b"B")

        assert first == expected, (
            f"Expected first order {expected}, got {first}"
        )

        print("PASS: Existing queued order preserved.")
        print("Verified first order:", first)

    finally:
        buffer.close()


if __name__ == "__main__":
    main()
