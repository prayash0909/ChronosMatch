
from order import Order
from matching_engine import MatchingEngine
from time import perf_counter

engine = MatchingEngine()

total_orders = 1000
start = perf_counter()

# Pehle 500 SELL orders add karo
for i in range(500):
    order = Order(
        order_id=f"S{i}",
        symbol="AAPL",
        side="SELL",
        price=101,
        quantity=10,
        timestamp=i + 1
    )
    engine.submit_order(order)

# Phir 500 BUY orders match karo
total_trades = 0

for i in range(500):
    order = Order(
        order_id=f"B{i}",
        symbol="AAPL",
        side="BUY",
        price=101,
        quantity=10,
        timestamp=1001 + i
    )
    trades = engine.submit_order(order)
    total_trades += len(trades)

elapsed = perf_counter() - start

print("Total orders submitted:", total_orders)
print("Total trades executed:", total_trades)
print("Elapsed time (seconds):", round(elapsed, 4))
print("Orders processed per second:", round(total_orders / elapsed))

assert total_trades == 500
assert len(engine.order_book.sell_orders) == 0
assert len(engine.order_book.buy_orders) == 0

print("PASS: Stress test completed successfully!")
