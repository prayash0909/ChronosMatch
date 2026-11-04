import pytest

from server import ChronosService


@pytest.fixture
def service(tmp_path):
    return ChronosService(db_path=tmp_path / "test_trades.db")


@pytest.mark.parametrize(
    "invalid_price",
    [0, -10, float("nan"), float("inf"), float("-inf"), 1_000_000_001],
)
def test_invalid_prices_are_rejected_without_consuming_order_id(
    service, invalid_price
):
    with pytest.raises(ValueError):
        service.submit({
            "symbol": "AAPL",
            "side": "BUY",
            "price": invalid_price,
            "quantity": 5,
        })

    assert service.next_id == 1


def test_valid_price_is_accepted(service):
    result = service.submit({
        "symbol": "AAPL",
        "side": "BUY",
        "price": 100.50,
        "quantity": 5,
    })

    assert result["ok"] is True
    assert result["order"]["price"] == 100.50
    assert result["order"]["order_id"] == "1"
    assert service.next_id == 2
