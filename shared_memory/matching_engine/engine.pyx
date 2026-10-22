
# cython: language_level=3

import time
import heapq


def match_order_stream(
    shared_buffer,
    shutdown_wrapper,
    trade_callback=None,
    verbose=False
):
    # SELL: lowest price first, then earliest sequence.
    sell_orders = []

    # BUY: highest price first, then earliest sequence.
    buy_orders = []

    sequence = 0

    if verbose:
        print("ChronosMatch matching engine started...")

    while not shutdown_wrapper[0]:
        order = shared_buffer.read_next_order()

        if order is None:
            time.sleep(0.001)
            continue

        order_id, price, qty, side = order

        side = side.decode() if isinstance(side, bytes) else side
        qty = int(qty)
        price = float(price)

        if qty <= 0 or side not in ("B", "S"):
            continue

        sequence += 1

        if verbose:
            print(
                f"Received: ID={order_id}, Side={side}, "
                f"Price={price}, Qty={qty}"
            )

        if side == "B":
            # Match incoming BUY against the best SELL orders.
            while qty > 0 and sell_orders:
                resting = sell_orders[0][2]

                if resting["price"] > price:
                    break

                traded_qty = min(qty, resting["qty"])

                if verbose:
                    print(
                        f"TRADE: Buy ID={order_id}, "
                        f"Sell ID={resting['id']}, "
                        f"Price={resting['price']}, "
                        f"Qty={traded_qty}"
                    )

                if trade_callback is not None:
                    trade_callback(
                        order_id,
                        resting["id"],
                        resting["price"],
                        traded_qty
                    )

                qty -= traded_qty
                resting["qty"] -= traded_qty

                if resting["qty"] == 0:
                    heapq.heappop(sell_orders)

            if qty > 0:
                heapq.heappush(
                    buy_orders,
                    (
                        -price,
                        sequence,
                        {
                            "id": order_id,
                            "price": price,
                            "qty": qty,
                            "sequence": sequence
                        }
                    )
                )

        else:
            # Match incoming SELL against the best BUY orders.
            while qty > 0 and buy_orders:
                resting = buy_orders[0][2]

                if resting["price"] < price:
                    break

                traded_qty = min(qty, resting["qty"])

                if verbose:
                    print(
                        f"TRADE: Buy ID={resting['id']}, "
                        f"Sell ID={order_id}, "
                        f"Price={resting['price']}, "
                        f"Qty={traded_qty}"
                    )

                if trade_callback is not None:
                    trade_callback(
                        resting["id"],
                        order_id,
                        resting["price"],
                        traded_qty
                    )

                qty -= traded_qty
                resting["qty"] -= traded_qty

                if resting["qty"] == 0:
                    heapq.heappop(buy_orders)

            if qty > 0:
                heapq.heappush(
                    sell_orders,
                    (
                        price,
                        sequence,
                        {
                            "id": order_id,
                            "price": price,
                            "qty": qty,
                            "sequence": sequence
                        }
                    )
                )

    if verbose:
        print("ChronosMatch matching engine stopped.")
