from shared_memory.buffer_experiment import SharedMemoryBuffer


def main():
    buffer = SharedMemoryBuffer(size=128)
    buffer.reset_buffer()

    total_orders = 10000
    capacity = buffer.capacity
    expected_id = 1
    received = 0

    try:
        for order_id in range(1, total_orders + 1):

            while True:
                try:
                    buffer.write_order(
                        order_id,
                        float(order_id),
                        1,
                        b"B"
                    )
                    break
                except BufferError:
                    order = buffer.read_next_order()

                    if order is None:
                        raise RuntimeError("Unexpected empty queue")

                    assert order[0] == expected_id, (
                        f"FIFO mismatch: expected {expected_id}, "
                        f"got {order[0]}"
                    )

                    assert order[1] == float(expected_id)
                    expected_id += 1
                    received += 1

        # Drain remaining orders.
        while True:
            order = buffer.read_next_order()

            if order is None:
                break

            assert order[0] == expected_id, (
                f"FIFO mismatch: expected {expected_id}, "
                f"got {order[0]}"
            )

            assert order[1] == float(expected_id)
            expected_id += 1
            received += 1

        assert received == total_orders
        assert expected_id == total_orders + 1

        write_seq, read_seq = __import__("struct").unpack(
            "<QQ",
            buffer.mm[8:24]
        )

        assert write_seq == total_orders
        assert read_seq == total_orders

        print("PASS: Repeated wraparound stress test.")
        print(f"Total orders verified: {received}")
        print(f"Ring buffer capacity: {capacity}")
        print(f"Wraparound cycles: {total_orders // capacity}")
        print(f"Final counters: write={write_seq}, read={read_seq}")

    finally:
        buffer.close()


if __name__ == "__main__":
    main()
