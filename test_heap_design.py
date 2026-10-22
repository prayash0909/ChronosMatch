
import heapq

# SELL: lowest price first, then earliest sequence
sell_heap = []

# BUY: highest price first, then earliest sequence
buy_heap = []

sequence = 0

def add_sell(order_id, price, qty):
    global sequence
    sequence += 1
    heapq.heappush(
        sell_heap,
        (price, sequence, order_id, qty)
    )

def add_buy(order_id, price, qty):
    global sequence
    sequence += 1
    heapq.heappush(
        buy_heap,
        (-price, sequence, order_id, qty)
    )

add_sell("S1", 101.0, 5)
add_sell("S2", 100.0, 3)
add_sell("S3", 100.0, 2)

add_buy("B1", 99.0, 4)
add_buy("B2", 102.0, 1)

print("Best SELL:", sell_heap[0])
print("Best BUY:", buy_heap[0])
