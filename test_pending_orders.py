
from order import Order
from matching_engine.core import MatchingEngine

engine = MatchingEngine()

# Add a BUY order that will remain pending
buy = Order("B101", "AAPL", "BUY", 99.0, 5)
engine.submit_order(buy)

# Add a SELL order at a higher price
sell = Order("S101", "AAPL", "SELL", 105.0, 3)
engine.submit_order(sell)

print("\n===== PENDING BUY ORDERS =====")
for order in engine.order_book.buy_orders:
    print(order.order_id, order.symbol, order.price,
          order.remaining_quantity)

print("\n===== PENDING SELL ORDERS =====")
for order in engine.order_book.sell_orders:
    print(order.order_id, order.symbol, order.price,
          order.remaining_quantity)
