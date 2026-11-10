from order import Order
from matching_engine.core import MatchingEngine


class FakeLedger:
    def __init__(self):
        self.records = []

    def record_trade(self, **kwargs):
        self.records.append(kwargs)


def create_engine():
    return MatchingEngine(ledger=FakeLedger())


def test_each_symbol_has_independent_order_book():
    engine = create_engine()

    aapl = engine.order_book.get_book("AAPL")
    googl = engine.order_book.get_book("GOOGL")

    assert aapl is not googl
    assert engine.order_books["AAPL"] is aapl
    assert engine.order_books["GOOGL"] is googl


def test_orders_are_stored_in_correct_books():
    engine = create_engine()

    aapl_sell = Order("S1", "AAPL", "SELL", 100, 5, timestamp=1)
    googl_sell = Order("S2", "GOOGL", "SELL", 200, 5, timestamp=2)

    engine.submit_order(aapl_sell)
    engine.submit_order(googl_sell)

    assert aapl_sell in engine.order_books["AAPL"].sell_orders
    assert googl_sell in engine.order_books["GOOGL"].sell_orders

    assert googl_sell not in engine.order_books["AAPL"].sell_orders
    assert aapl_sell not in engine.order_books["GOOGL"].sell_orders


def test_cancellation_is_symbol_specific():
    engine = create_engine()

    aapl = Order("B1", "AAPL", "BUY", 100, 5, timestamp=1)
    googl = Order("B2", "GOOGL", "BUY", 200, 5, timestamp=2)

    engine.submit_order(aapl)
    engine.submit_order(googl)

    assert engine.order_book.cancel_order("B1", "AAPL") is True

    assert aapl not in engine.order_books["AAPL"].buy_orders
    assert googl in engine.order_books["GOOGL"].buy_orders


def test_matching_only_uses_its_symbol_book():
    engine = create_engine()

    aapl_sell = Order("S3", "AAPL", "SELL", 100, 5, timestamp=1)
    googl_buy = Order("B3", "GOOGL", "BUY", 100, 5, timestamp=2)

    engine.submit_order(aapl_sell)
    trades = engine.submit_order(googl_buy)

    assert trades == []
    assert aapl_sell.remaining_quantity == 5
    assert googl_buy.remaining_quantity == 5


def test_symbols_are_case_insensitive():
    engine = create_engine()

    lower = engine.order_book.get_book("aapl")
    upper = engine.order_book.get_book("AAPL")

    assert lower is upper