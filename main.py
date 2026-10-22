
from order import Order
from matching_engine.core import MatchingEngine


engine = MatchingEngine()


sell_order = Order(
    order_id="S001",
    symbol="AAPL",
    side="SELL",
    price=100,
    quantity=6
)

print("Submitting sell order...")
print(engine.submit_order(sell_order))


buy_order = Order(
    order_id="B001",
    symbol="AAPL",
    side="BUY",
    price=100,
    quantity=10
)

print("\nSubmitting buy order...")
print(engine.submit_order(buy_order))

print("\nRemaining buy quantity:", buy_order.remaining_quantity)
print("Remaining sell quantity:", sell_order.remaining_quantity)

print("\nPending buy orders:")
for order in engine.order_book.buy_orders:
    print(order.order_id, order.price, order.remaining_quantity)

print("\nCompleted trades:")
for trade in engine.trades:
    print(trade)
