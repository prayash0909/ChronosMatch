import tempfile
import unittest
from pathlib import Path

from server import ChronosService


class ChronosServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.service = ChronosService(Path(self.temp_dir.name) / "trades.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_crossing_orders_match_and_persist_trade(self):
        sell = self.service.submit({
            "symbol": "AAPL", "side": "SELL", "price": 100.0, "quantity": 3
        })
        self.assertEqual(sell["new_trades"], [])

        buy = self.service.submit({
            "symbol": "AAPL", "side": "BUY", "price": 101.0, "quantity": 2
        })
        self.assertEqual(len(buy["new_trades"]), 1)
        self.assertEqual(buy["new_trades"][0]["price"], 100.0)
        self.assertEqual(buy["new_trades"][0]["quantity"], 2)
        state = self.service.state()
        self.assertEqual(state["trades_matched"], 1)
        self.assertEqual(len(state["order_book"]["asks"]), 1)
        self.assertEqual(state["order_book"]["asks"][0]["remaining_quantity"], 1)
        self.assertEqual(state["analytics"]["total_trades"], 1)

    def test_rejects_invalid_orders(self):
        cases = [
            {"symbol": "AAPL", "side": "HOLD", "price": 100, "quantity": 1},
            {"symbol": "AAPL", "side": "BUY", "price": -1, "quantity": 1},
            {"symbol": "AAPL", "side": "BUY", "price": 100, "quantity": 0},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    self.service.submit(payload)

    def test_reset_clears_book_but_keeps_trade_ledger(self):
        self.service.submit({
            "symbol": "AAPL", "side": "SELL", "price": 100, "quantity": 1
        })
        self.service.submit({
            "symbol": "AAPL", "side": "BUY", "price": 100, "quantity": 1
        })
        state = self.service.reset()
        self.assertEqual(state["orders_processed"], 0)
        self.assertEqual(state["trades_matched"], 0)
        self.assertEqual(len(state["trades"]), 1)


if __name__ == "__main__":
    unittest.main()
