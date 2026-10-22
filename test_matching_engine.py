import threading
import unittest

from run_engine import match_order_stream


class InMemoryOrderQueue:
    def __init__(self, orders, shutdown):
        self.orders = iter(orders)
        self.shutdown = shutdown

    def read_next_order(self):
        try:
            return next(self.orders)
        except StopIteration:
            self.shutdown[0] = True
            return None


class MatchingEngineTests(unittest.TestCase):
    def run_orders(self, orders):
        shutdown = [False]
        queue = InMemoryOrderQueue(orders, shutdown)
        trades = []
        engine_thread = threading.Thread(
            target=match_order_stream,
            args=(queue, shutdown, lambda *trade: trades.append(trade))
        )

        engine_thread.start()
        engine_thread.join(timeout=5)

        if engine_thread.is_alive():
            shutdown[0] = True
            engine_thread.join(timeout=1)
            self.fail("Matching engine did not stop after consuming orders")

        return trades

    def test_matches_best_price_first(self):
        trades = self.run_orders([
            (101, 101.0, 1, b"S"),
            (102, 100.0, 1, b"S"),
            (103, 101.0, 1, b"B"),
        ])

        self.assertEqual(trades, [(103, 102, 100.0, 1)])

    def test_matches_oldest_order_first_at_equal_price(self):
        trades = self.run_orders([
            (201, 100.0, 2, b"S"),
            (202, 100.0, 2, b"S"),
            (203, 100.0, 3, b"B"),
        ])

        self.assertEqual(trades, [
            (203, 201, 100.0, 2),
            (203, 202, 100.0, 1),
        ])

    def test_partial_fills_preserve_remaining_quantity(self):
        trades = self.run_orders([
            (301, 100.0, 5, b"S"),
            (302, 100.0, 2, b"B"),
            (303, 101.0, 4, b"B"),
            (304, 99.0, 1, b"S"),
        ])

        self.assertEqual(trades, [
            (302, 301, 100.0, 2),
            (303, 301, 100.0, 3),
            (303, 304, 101.0, 1),
        ])


if __name__ == "__main__":
    unittest.main()
