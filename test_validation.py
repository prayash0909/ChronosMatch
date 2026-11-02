
import pytest
from order import Order


def should_reject(description, **kwargs):
    with pytest.raises(ValueError):
        Order(**kwargs)


@pytest.mark.parametrize(
    "description,kwargs",
    [
        (
            "negative price",
            dict(order_id="T001", symbol="AAPL", side="BUY",
                 price=-10, quantity=5),
        ),
        (
            "zero price",
            dict(order_id="T005", symbol="AAPL", side="BUY",
                 price=0, quantity=5),
        ),
        (
            "zero quantity",
            dict(order_id="T002", symbol="AAPL", side="BUY",
                 price=100, quantity=0),
        ),
        (
            "negative quantity",
            dict(order_id="T006", symbol="AAPL", side="BUY",
                 price=100, quantity=-5),
        ),
        (
            "invalid side",
            dict(order_id="T003", symbol="AAPL", side="HOLD",
                 price=100, quantity=5),
        ),
        (
            "empty order ID",
            dict(order_id="", symbol="AAPL", side="BUY",
                 price=100, quantity=5),
        ),
        (
            "empty symbol",
            dict(order_id="T007", symbol="", side="BUY",
                 price=100, quantity=5),
        ),
    ],
)
def test_invalid_orders_are_rejected(description, kwargs):
    should_reject(description, **kwargs)


def test_symbol_is_normalized_to_uppercase():
    order = Order(
        order_id="T008",
        symbol="aapl",
        side="BUY",
        price=100,
        quantity=5,
    )
    assert order.symbol == "AAPL"


def test_side_is_normalized_to_uppercase():
    order = Order(
        order_id="T009",
        symbol="AAPL",
        side="buy",  # type: ignore[arg-type]
        price=100,
        quantity=5,
    )
    assert order.side == "BUY"
@pytest.mark.parametrize(
    "invalid_price",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_non_finite_prices_are_rejected(invalid_price):
    with pytest.raises(
        ValueError,
        match="Price must be a finite positive number",
    ):
        Order(
            order_id="T010",
            symbol="AAPL",
            side="BUY",
            price=invalid_price,
            quantity=5,
        )
@pytest.mark.parametrize(
    "invalid_quantity",
    [
        2.5,
        1.7,
        True,
        False,
        "5",
    ],
)
def test_non_integer_quantities_are_rejected(invalid_quantity):
    with pytest.raises(
        ValueError,
        match="Quantity must be a positive integer",
    ):
        Order(
            order_id="T011",
            symbol="AAPL",
            side="BUY",
            price=100,
            quantity=invalid_quantity,
        )