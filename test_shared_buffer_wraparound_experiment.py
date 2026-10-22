
from shared_memory.buffer_experiment import SharedMemoryBuffer


def main():
    buffer = SharedMemoryBuffer(size=128)
    buffer.reset_buffer()

    try:
        capacity = buffer.capacity
        assert capacity >= 3, f"Capacity too small: {capacity}"

        # Fill the queue.
        for i in range(capacity):
            buffer.write_order(9600 + i, 100.0 + i, 1, b"B")

        # Free two slots.
        first = buffer.read_next_order()
        second = buffer.read_next_order()

        assert first is not None, "Expected the first queued order"
        assert second is not None, "Expected the second queued order"
        assert first[0] == 9600
        assert second[0] == 9601

        # Write two more orders; the write position wraps around.
        buffer.write_order(9600 + capacity, 200.0, 1, b"S")
        buffer.write_order(9601 + capacity, 201.0, 1, b"S")

        # Remaining old orders must come before new orders.
        remaining = []

        while True:
            order = buffer.read_next_order()
            if order is None:
                break
            remaining.append(order)

        expected_ids = (
            list(range(9602, 9600 + capacity))
            + [9600 + capacity, 9601 + capacity]
        )
        actual_ids = [order[0] for order in remaining]

        assert actual_ids == expected_ids, (
            f"Expected IDs {expected_ids}, got {actual_ids}"
        )

        print("PASS: Circular queue wraparound verified.")
        print("Verified order IDs:", actual_ids)

    finally:
        buffer.close()


if __name__ == "__main__":
    main()