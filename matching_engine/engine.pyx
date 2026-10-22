
# cython: language_level=3

import time


def match_order_stream(
    shared_buffer,
    shutdown_wrapper,
    trade_callback=None,
    verbose=False
):
    last_processed_id = None
    buy_orders = []
    sell_orders = []
    sequence = 0

    if verbose:
        print("ChronosMatch matching engine started...")

    while not shutdown_wrapper[0]:
        order = shared_buffer.read_next_order()

        if order is None:
            time.sleep(0.001)
            continue

        order_id, price, qty, side = order

        if order_id == last_processed_id:
            time.sleep(0.001)
            continue

        last_processed_id = order_id
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
            while qty > 0 and sell_orders:
                best_index = min(
                    range(len(sell_orders)),
                    key=lambda i: (
                        sell_orders[i]["price"],
                        sell_orders[i]["sequence"]
                    )
                )

                resting = sell_orders[best_index]

                if resting["price"] > price:
                    break

                traded_qty = min(qty, resting["qty"])

                if verbose:
                    print(
                        f"TRADE: Buy ID={order_id}, "
                        f"Sell ID={resting['id']}, "
                        f"Price={resting['price']}, Qty={traded_qty}"
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
                    sell_orders.pop(best_index)

            if qty > 0:
                buy_orders.append({
                    "id": order_id,
                    "price": price,
                    "qty": qty,
                    "sequence": sequence
                })

        else:
            while qty > 0 and buy_orders:
                best_index = max(
                    range(len(buy_orders)),
                    key=lambda i: (
                        buy_orders[i]["price"],
                        -buy_orders[i]["sequence"]
                    )
                )

                resting = buy_orders[best_index]

                if resting["price"] < price:
                    break

                traded_qty = min(qty, resting["qty"])

                if verbose:
                    print(
                        f"TRADE: Buy ID={resting['id']}, "
                        f"Sell ID={order_id}, "
                        f"Price={resting['price']}, Qty={traded_qty}"
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
                    buy_orders.pop(best_index)

            if qty > 0:
                sell_orders.append({
                    "id": order_id,
                    "price": price,
                    "qty": qty,
                    "sequence": sequence
                })

    if verbose:
        print("ChronosMatch matching engine stopped.")
