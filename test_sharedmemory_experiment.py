from shared_memory.buffer_sharedmemory_experiment import (
    SharedMemoryBufferExperiment
)


def test_empty_queue():
    buffer = SharedMemoryBufferExperiment(size=128)
    try:
        assert buffer.read_next_order() is None
        print("PASS: Empty queue")
    finally:
        buffer.close(unlink=True)


def test_full_queue():
    buffer = SharedMemoryBufferExperiment(size=128)
    try:
        for i in range(buffer.capacity):
            buffer.write_order(i + 1, 100.0, 1, b"B")

        try:
            buffer.write_order(9999, 100.0, 1, b"S")
            raise AssertionError("Expected queue-full error")
        except BufferError:
            print("PASS: Full queue protection")
    finally:
        buffer.close(unlink=True)


def test_wraparound():
    buffer = SharedMemoryBufferExperiment(size=128)
    try:
        capacity = buffer.capacity

        for i in range(capacity):
            buffer.write_order(i + 1, 100.0, 1, b"B")

        for i in range(capacity):
            order = buffer.read_next_order()
            assert order[0] == i + 1

        for i in range(capacity):
            buffer.write_order(100 + i, 101.0, 2, b"S")

        for i in range(capacity):
            order = buffer.read_next_order()
            assert order[0] == 100 + i

        assert buffer.read_next_order() is None
        print("PASS: Queue wraparound")
    finally:
        buffer.close(unlink=True)


if __name__ == "__main__":
    test_empty_queue()
    test_full_queue()
    test_wraparound()
    print("ALL QUEUE TESTS PASSED")
