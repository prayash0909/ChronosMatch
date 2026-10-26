
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
