
from order import Order
from matching_engine.core import MatchingEngine

engine = MatchingEngine()

sell = Order("S201", "AAPL", "SELL", 100.0, 10)
buy = Order("B201", "AAPL", "BUY", 100.0, 4)

print("Submitting SELL order...")
print(engine.submit_order(sell))

print("\nSubmitting BUY order...")
print(engine.submit_order(buy))

print("\n===== PARTIAL FILL RESULT =====")
print("SELL remaining:", sell.remaining_quantity)
print("BUY remaining:", buy.remaining_quantity)

print("\n===== PENDING SELL ORDERS =====")
for order in engine.order_book.sell_orders:
    print(order.order_id, order.remaining_quantity)

print("\n===== COMPLETED TRADES =====")
for trade in engine.trades:
    print(trade)
