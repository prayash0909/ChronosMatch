
import pytest

from order import Order
from order_book import OrderBook


def test_best_sell_price_first():
    book = OrderBook()
    book.add_order(Order("S1", "AAPL", "SELL", 101, 5))
    book.add_order(Order("S2", "AAPL", "SELL", 99, 3))

    best = book.best_opposite("AAPL", "BUY")

    assert best is not None
    assert best.order_id == "S2"


def test_orders_are_isolated_by_symbol():
    book = OrderBook()
    book.add_order(Order("S1", "AAPL", "SELL", 101, 5))
    book.add_order(Order("S2", "GOOGL", "SELL", 90, 2))

    best = book.best_opposite("AAPL", "BUY")

    assert best is not None
    assert best.order_id == "S1"


def test_removed_order_is_not_returned():
    book = OrderBook()
    first = Order("S1", "AAPL", "SELL", 99, 3)
    second = Order("S2", "AAPL", "SELL", 101, 5)

    book.add_order(first)
    book.add_order(second)
    book.remove_order(first)

    best = book.best_opposite("AAPL", "BUY")

    assert best is not None
    assert best.order_id == "S2"


def test_best_buy_price_first():
    book = OrderBook()
    book.add_order(Order("B1", "AAPL", "BUY", 99, 2))
    book.add_order(Order("B2", "AAPL", "BUY", 101, 4))

    best = book.best_opposite("AAPL", "SELL")

    assert best is not None
    assert best.order_id == "B2"



def test_invalid_order_side_raises_error():
    invalid_side = "HOLD"

    with pytest.raises(ValueError, match="Side must be BUY or SELL"):
        Order("X1", "AAPL", invalid_side, 100, 1)  # type: ignore[arg-type]


def test_best_opposite_returns_none_when_no_candidate_exists():
    book = OrderBook()
    book.add_order(Order("S1", "AAPL", "SELL", 101, 5))

    assert book.best_opposite("AAPL", "SELL") is None
    assert book.best_opposite("MSFT", "BUY") is None


def test_best_opposite_rejects_invalid_side():
    book = OrderBook()

    with pytest.raises(ValueError, match="Side must be BUY or SELL"):
        book.best_opposite("AAPL", "HOLD")  # type: ignore[arg-type]
def test_sell_orders_follow_fifo_at_same_price():
    book = OrderBook()

    first = Order("S1", "AAPL", "SELL", 100, 5, timestamp=100)
    second = Order("S2", "AAPL", "SELL", 100, 5, timestamp=200)

    book.add_order(first)
    book.add_order(second)

    best = book.best_opposite("AAPL", "BUY")

    assert best is first


def test_buy_orders_follow_fifo_at_same_price():
    book = OrderBook()

    first = Order("B1", "AAPL", "BUY", 100, 5, timestamp=100)
    second = Order("B2", "AAPL", "BUY", 100, 5, timestamp=200)

    book.add_order(first)
    book.add_order(second)

    best = book.best_opposite("AAPL", "SELL")

    assert best is first