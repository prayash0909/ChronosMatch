import struct
import unittest
import uuid

from shared_memory.buffer import SharedMemoryBuffer


class SharedMemoryBufferTests(unittest.TestCase):
    def create_buffer(self, size=256):
        tag_name = f"Local\\ChronosMatchTest-{uuid.uuid4().hex}"
        return SharedMemoryBuffer(size=size, tag_name=tag_name)

    def test_reads_burst_orders_in_fifo_order(self):
        buffer = self.create_buffer()
        orders = [
            (order_id, 100.0 + order_id, order_id, b"B")
            for order_id in range(1, 6)
        ]

        try:
            for order in orders:
                buffer.write_order(*order)

            self.assertEqual(
                [buffer.read_next_order() for _ in orders],
                orders
            )
            self.assertIsNone(buffer.read_next_order())
        finally:
            buffer.close()

    def test_full_queue_rejects_order_without_overwriting(self):
        buffer = self.create_buffer(size=24 + 2 * struct.calcsize("Qdic"))
        try:
            first = (1, 100.0, 1, b"B")
            second = (2, 101.0, 2, b"S")
            buffer.write_order(*first)
            buffer.write_order(*second)

            with self.assertRaises(BufferError):
                buffer.write_order(3, 102.0, 3, b"B")

            self.assertEqual(buffer.read_next_order(), first)
            self.assertEqual(buffer.read_next_order(), second)
        finally:
            buffer.close()

    def test_reuses_slots_after_orders_are_consumed(self):
        buffer = self.create_buffer(size=24 + 2 * struct.calcsize("Qdic"))
        try:
            orders = [
                (order_id, 100.0, 1, b"B")
                for order_id in range(1, 5)
            ]
            for order in orders[:2]:
                buffer.write_order(*order)

            self.assertEqual(buffer.read_next_order(), orders[0])
            buffer.write_order(*orders[2])
            self.assertEqual(buffer.read_next_order(), orders[1])
            buffer.write_order(*orders[3])

            self.assertEqual(
                [buffer.read_next_order() for _ in range(2)],
                orders[2:]
            )
            self.assertIsNone(buffer.read_next_order())
        finally:
            buffer.close()


if __name__ == "__main__":
    unittest.main()
