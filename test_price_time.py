
from order import Order
from matching_engine import MatchingEngine

engine = MatchingEngine()

# Same price par do SELL orders
sell1 = Order("S301", "AAPL", "SELL", 100, 5, timestamp=100)
sell2 = Order("S302", "AAPL", "SELL", 100, 5, timestamp=200)

engine.submit_order(sell1)
engine.submit_order(sell2)

# BUY order dono SELL orders ko match kar sakta hai
buy = Order("B301", "AAPL", "BUY", 100, 7, timestamp=300)
trades = engine.submit_order(buy)

print("Executed trades:")
for trade in trades:
    print(trade)

print("\nRemaining SELL quantities:")
print("S301:", sell1.remaining_quantity)
print("S302:", sell2.remaining_quantity)

assert trades[0]["matched_order_id"] == "S301"
assert trades[1]["matched_order_id"] == "S302"
assert sell1.remaining_quantity == 0
assert sell2.remaining_quantity == 3

print("\nPASS: Price-Time Priority works correctly!")
