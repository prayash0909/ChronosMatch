
from order import Order

def should_reject(description, **kwargs):
    try:
        Order(**kwargs)
    except ValueError:
        print(f"PASS: Rejected {description}")
        return
    raise AssertionError(f"FAIL: Accepted {description}")


should_reject(
    "negative price",
    order_id="T001", symbol="AAPL", side="BUY",
    price=-10, quantity=5
)

should_reject(
    "zero quantity",
    order_id="T002", symbol="AAPL", side="BUY",
    price=100, quantity=0
)

should_reject(
    "invalid side",
    order_id="T003", symbol="AAPL", side="HOLD",
    price=100, quantity=5
)

should_reject(
    "empty order ID",
    order_id="", symbol="AAPL", side="BUY",
    price=100, quantity=5
)

print("\nAll validation tests passed!")
