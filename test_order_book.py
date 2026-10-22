
from order import Order
from order_book import OrderBook

book = OrderBook()

# Add SELL orders for AAPL
s1 = Order("S1", "AAPL", "SELL", 101, 5)
s2 = Order("S2", "AAPL", "SELL", 99, 3)

# Add a SELL order for another symbol
s3 = Order("S3", "GOOGL", "SELL", 90, 2)

book.add_order(s1)
book.add_order(s2)
book.add_order(s3)

# Test best price for AAPL
best = book.best_opposite("AAPL", "BUY")
assert best is not None, "Expected an AAPL SELL order"
print("Best SELL for AAPL:", best.order_id)

# Remove the best AAPL SELL order
book.remove_order(s2)

best = book.best_opposite("AAPL", "BUY")
assert best is not None, "Expected another AAPL SELL order"
print("Next best SELL for AAPL:", best.order_id)

# Verify symbol isolation
best_googl = book.best_opposite("GOOGL", "BUY")
assert best_googl is not None, "Expected a GOOGL SELL order"
print("Best SELL for GOOGL:", best_googl.order_id)
