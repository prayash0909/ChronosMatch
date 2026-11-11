
from order import Order
from matching_engine.core import MatchingEngine


class FakeLedger:
    def __init__(self):
        self.records = []

    def record_trade(self, **kwargs):
        self.records.append(kwargs)


def create_engine():
    return MatchingEngine(ledger=FakeLedger())


def test_cancel_order_by_id():
    engine = create_engine()

    order = Order("B1", "AAPL", "BUY", 100, 5)
    engine.submit_order(order)

    assert engine.cancel_order("B1") is True
    assert order not in engine.order_books["AAPL"].buy_orders


def test_cancel_order_with_symbol():
    engine = create_engine()

    order = Order("B2", "GOOGL", "BUY", 200, 5)
    engine.submit_order(order)

    assert engine.cancel_order("B2", "GOOGL") is True
    assert order not in engine.order_books["GOOGL"].buy_orders


def test_wrong_symbol_does_not_cancel_order():
    engine = create_engine()

    order = Order("B3", "AAPL", "BUY", 100, 5)
    engine.submit_order(order)

    assert engine.cancel_order("B3", "GOOGL") is False
    assert order in engine.order_books["AAPL"].buy_orders


def test_unknown_order_returns_false():
    engine = create_engine()

    assert engine.cancel_order("UNKNOWN") is False


def test_cancel_one_symbol_preserves_other_symbol_orders():
    engine = create_engine()

    aapl = Order("B4", "AAPL", "BUY", 100, 5)
    googl = Order("B5", "GOOGL", "BUY", 200, 5)

    engine.submit_order(aapl)
    engine.submit_order(googl)

    assert engine.cancel_order("B4", "AAPL") is True

    assert aapl not in engine.order_books["AAPL"].buy_orders
    assert googl in engine.order_books["GOOGL"].buy_orders


def test_cancel_already_filled_order_returns_false():
    engine = create_engine()

    sell = Order("S1", "AAPL", "SELL", 100, 5)
    buy = Order("B6", "AAPL", "BUY", 100, 5)

    engine.submit_order(sell)
    engine.submit_order(buy)

    assert buy.is_filled
    assert engine.cancel_order("B6") is False
