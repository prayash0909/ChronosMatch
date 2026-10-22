
from order import Order
from matching_engine import MatchingEngine

engine = MatchingEngine()

# AAPL SELL order
sell_aapl = Order(
    order_id="S401",
    symbol="AAPL",
    side="SELL",
    price=100,
    quantity=5,
    timestamp=100
)

# GOOGL BUY order: price same hai, lekin symbol different hai
buy_googl = Order(
    order_id="B401",
    symbol="GOOGL",
    side="BUY",
    price=100,
    quantity=5,
    timestamp=200
)

engine.submit_order(sell_aapl)
trades = engine.submit_order(buy_googl)

assert trades == []
assert sell_aapl.remaining_quantity == 5
assert buy_googl.remaining_quantity == 5

print("PASS: Different symbols do not match!")

# Ab AAPL BUY bhejkar correct matching verify karte hain
buy_aapl = Order(
    order_id="B402",
    symbol="AAPL",
    side="BUY",
    price=100,
    quantity=3,
    timestamp=300
)

trades = engine.submit_order(buy_aapl)

assert len(trades) == 1
assert trades[0]["matched_order_id"] == "S401"
assert sell_aapl.remaining_quantity == 2

print("PASS: Same symbols match correctly!")
print("AAPL SELL remaining:", sell_aapl.remaining_quantity)
