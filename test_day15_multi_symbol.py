from order import Order
from matching_engine.core import MatchingEngine


class FakeLedger:
    def __init__(self):
        self.records = []

    def record_trade(self, **kwargs):
        self.records.append(kwargs)


def create_engine():
    ledger = FakeLedger()
    return MatchingEngine(ledger=ledger), ledger


def test_different_symbols_never_match():
    engine, ledger = create_engine()

    aapl_sell = Order("S1", "AAPL", "SELL", 100, 5, timestamp=1)
    googl_buy = Order("B1", "GOOGL", "BUY", 100, 5, timestamp=2)

    engine.submit_order(aapl_sell)
    trades = engine.submit_order(googl_buy)

    assert trades == []
    assert aapl_sell.remaining_quantity == 5
    assert googl_buy.remaining_quantity == 5
    assert ledger.records == []


def test_same_symbol_matches_correctly():
    engine, ledger = create_engine()

    sell = Order("S2", "AAPL", "SELL", 100, 5, timestamp=1)
    buy = Order("B2", "aapl", "BUY", 100, 3, timestamp=2)

    engine.submit_order(sell)
    trades = engine.submit_order(buy)

    assert len(trades) == 1
    assert trades[0]["symbol"] == "AAPL"
    assert trades[0]["matched_order_id"] == "S2"
    assert trades[0]["quantity"] == 3
    assert sell.remaining_quantity == 2
    assert buy.remaining_quantity == 0
    assert len(ledger.records) == 1


def test_partial_fills_are_isolated_by_symbol():
    engine, ledger = create_engine()

    aapl_sell = Order("AS1", "AAPL", "SELL", 100, 5, timestamp=1)
    googl_sell = Order("GS1", "GOOGL", "SELL", 200, 4, timestamp=2)

    engine.submit_order(aapl_sell)
    engine.submit_order(googl_sell)

    aapl_trades = engine.submit_order(
        Order("AB1", "AAPL", "BUY", 100, 2, timestamp=3)
    )
    googl_trades = engine.submit_order(
        Order("GB1", "GOOGL", "BUY", 200, 3, timestamp=4)
    )

    assert len(aapl_trades) == 1
    assert len(googl_trades) == 1

    assert aapl_trades[0]["symbol"] == "AAPL"
    assert googl_trades[0]["symbol"] == "GOOGL"

    assert aapl_sell.remaining_quantity == 3
    assert googl_sell.remaining_quantity == 1

    assert aapl_trades[0]["matched_order_id"] == "AS1"
    assert googl_trades[0]["matched_order_id"] == "GS1"


def test_cancellation_does_not_remove_another_symbol_order():
    engine, _ = create_engine()

    aapl_buy = Order("AB2", "AAPL", "BUY", 99, 5, timestamp=1)
    googl_buy = Order("GB2", "GOOGL", "BUY", 199, 5, timestamp=2)

    engine.submit_order(aapl_buy)
    engine.submit_order(googl_buy)

    assert engine.order_book.cancel_order("AB2") is True

    remaining_ids = {
        order.order_id for order in engine.order_book.buy_orders
    }

    assert "AB2" not in remaining_ids
    assert "GB2" in remaining_ids


def test_pending_orders_remain_separate_by_symbol():
    engine, _ = create_engine()

    aapl_buy = Order("AB3", "AAPL", "BUY", 99, 5, timestamp=1)
    googl_sell = Order("GS3", "GOOGL", "SELL", 205, 4, timestamp=2)

    engine.submit_order(aapl_buy)
    engine.submit_order(googl_sell)

    assert aapl_buy in engine.order_book.buy_orders
    assert googl_sell in engine.order_book.sell_orders

    assert engine.order_book.best_opposite("AAPL", "BUY") is None
    assert engine.order_book.best_opposite("GOOGL", "SELL") is None
