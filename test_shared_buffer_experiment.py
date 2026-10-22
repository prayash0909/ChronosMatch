
from shared_memory.buffer_experiment import SharedMemoryBuffer

def main():
    buffer = SharedMemoryBuffer(size=256)
    buffer.reset_buffer()

    try:
        # Write three orders.
        buffer.write_order(9401, 100.0, 2, b"B")
        buffer.write_order(9402, 101.0, 3, b"S")
        buffer.write_order(9403, 99.0, 1, b"B")

        # Read them back in insertion order.
        first = buffer.read_next_order()
        second = buffer.read_next_order()
        third = buffer.read_next_order()
        empty = buffer.read_next_order()

        assert first == (9401, 100.0, 2, b"B"), first
        assert second == (9402, 101.0, 3, b"S"), second
        assert third == (9403, 99.0, 1, b"B"), third
        assert empty is None, empty

        print("PASS: Shared buffer FIFO verified.")
        print("PASS: Empty queue returns None.")
        print("Verified orders:", first, second, third)

    finally:
        buffer.close()


if __name__ == "__main__":
    main()
