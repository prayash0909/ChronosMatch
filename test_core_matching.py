
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


def test_partial_fill_preserves_remaining_quantity():
    engine, ledger = create_engine()

    sell = Order("S301", "AAPL", "SELL", 100.0, 10)
    buy = Order("B301", "AAPL", "BUY", 100.0, 4)

    trades = engine.submit_order(sell)
    assert trades == []

    trades = engine.submit_order(buy)

    assert len(trades) == 1
    assert trades[0]["quantity"] == 4
    assert buy.remaining_quantity == 0
    assert sell.remaining_quantity == 6
    assert sell in engine.order_book.sell_orders
    assert len(ledger.records) == 1


def test_fully_filled_orders_are_removed():
    engine, ledger = create_engine()

    sell = Order("S302", "AAPL", "SELL", 100.0, 5)
    buy = Order("B302", "AAPL", "BUY", 100.0, 5)

    engine.submit_order(sell)
    trades = engine.submit_order(buy)

    assert len(trades) == 1
    assert sell.remaining_quantity == 0
    assert buy.remaining_quantity == 0
    assert sell not in engine.order_book.sell_orders
    assert buy not in engine.order_book.buy_orders
    assert len(ledger.records) == 1


def test_one_order_matches_multiple_resting_orders():
    engine, ledger = create_engine()

    first_sell = Order("S303", "AAPL", "SELL", 100.0, 2)
    second_sell = Order("S304", "AAPL", "SELL", 100.0, 3)
    incoming_buy = Order("B303", "AAPL", "BUY", 100.0, 4)

    engine.submit_order(first_sell)
    engine.submit_order(second_sell)

    trades = engine.submit_order(incoming_buy)

    assert [trade["quantity"] for trade in trades] == [2, 2]
    assert first_sell.remaining_quantity == 0
    assert second_sell.remaining_quantity == 1
    assert incoming_buy.remaining_quantity == 0
    assert first_sell not in engine.order_book.sell_orders
    assert second_sell in engine.order_book.sell_orders
    assert len(ledger.records) == 2
