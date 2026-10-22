import asyncio
import unittest

from market_sim.simulator import HighThroughputSimulator


class FakeBuffer:
    def __init__(self):
        self.orders = []

    def write_order(self, order_id, price, quantity, side):
        self.orders.append((order_id, price, quantity, side))


class MarketSimulatorTests(unittest.TestCase):
    def test_generates_requested_number_of_valid_orders(self):
        buffer = FakeBuffer()
        simulator = HighThroughputSimulator(buffer, target_orders_per_second=1_000_000, seed=7)
        shutdown = [False]
        asyncio.run(simulator.generate_market_ticks(shutdown, max_orders=25, report_every=0))

        self.assertEqual(len(buffer.orders), 25)
        self.assertEqual(simulator.generated, 25)
        self.assertTrue(all(row[2] > 0 and row[3] in (b"B", b"S") for row in buffer.orders))
        self.assertEqual(len({row[0] for row in buffer.orders}), 25)

    def test_rejects_non_positive_target_rate(self):
        with self.assertRaises(ValueError):
            HighThroughputSimulator(FakeBuffer(), target_orders_per_second=0)


if __name__ == "__main__":
    unittest.main()
