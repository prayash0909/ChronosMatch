# cython: language_level=3

import heapq
import time


def match_order_stream(
    shared_buffer,
    shutdown_wrapper,
    trade_callback=None,
    verbose=False,
    metrics_callback=None
):
    last_processed_id = None
    # Sell heap: lowest price first, then oldest sequence.
    sell_orders = []
    # Buy heap: highest price first (negative price), then oldest sequence.
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
            levels_cleared = 0
            order_started_ns = time.perf_counter_ns()

            while qty > 0 and sell_orders:
                best_price, _, resting = sell_orders[0]
                if best_price > price:
                    break

                traded_qty = min(qty, resting["qty"])
                trade_started_ns = time.perf_counter_ns()

                if verbose:
                    print(
                        f"TRADE: Buy ID={order_id}, "
                        f"Sell ID={resting['id']}, "
                        f"Price={best_price}, Qty={traded_qty}"
                    )

                if trade_callback is not None:
                    trade_callback(
                        order_id, resting["id"], best_price, traded_qty
                    )

                trade_latency_ns = time.perf_counter_ns() - trade_started_ns
                if metrics_callback is not None:
                    metrics_callback({
                        "buy_order_id": order_id,
                        "sell_order_id": resting["id"],
                        "price": best_price,
                        "quantity": traded_qty,
                        "latency_ns": trade_latency_ns,
                        "timestamp_ns": time.perf_counter_ns()
                    })

                levels_cleared += 1
                qty -= traded_qty
                resting["qty"] -= traded_qty

                if resting["qty"] == 0:
                    heapq.heappop(sell_orders)

            if verbose and levels_cleared > 1:
                elapsed_us = (time.perf_counter_ns() - order_started_ns) / 1000
                print(
                    f"[WHALE BUY] order={order_id} cleared "
                    f"{levels_cleared} ask levels in {elapsed_us:.1f} us"
                )

            if qty > 0:
                resting = {
                    "id": order_id,
                    "price": price,
                    "qty": qty,
                    "sequence": sequence
                }
                heapq.heappush(sell_orders, (price, sequence, resting)) if False else None
                # Resting buy orders belong in the buy heap.
                heapq.heappush(buy_orders, (-price, sequence, resting))

        else:
            levels_cleared = 0
            order_started_ns = time.perf_counter_ns()

            while qty > 0 and buy_orders:
                neg_best_price, _, resting = buy_orders[0]
                best_price = -neg_best_price
                if best_price < price:
                    break

                traded_qty = min(qty, resting["qty"])
                trade_started_ns = time.perf_counter_ns()

                if verbose:
                    print(
                        f"TRADE: Buy ID={resting['id']}, "
                        f"Sell ID={order_id}, "
                        f"Price={best_price}, Qty={traded_qty}"
                    )

                if trade_callback is not None:
                    trade_callback(
                        resting["id"], order_id, best_price, traded_qty
                    )

                trade_latency_ns = time.perf_counter_ns() - trade_started_ns
                if metrics_callback is not None:
                    metrics_callback({
                        "buy_order_id": resting["id"],
                        "sell_order_id": order_id,
                        "price": best_price,
                        "quantity": traded_qty,
                        "latency_ns": trade_latency_ns,
                        "timestamp_ns": time.perf_counter_ns()
                    })

                levels_cleared += 1
                qty -= traded_qty
                resting["qty"] -= traded_qty

                if resting["qty"] == 0:
                    heapq.heappop(buy_orders)

            if verbose and levels_cleared > 1:
                elapsed_us = (time.perf_counter_ns() - order_started_ns) / 1000
                print(
                    f"[WHALE SELL] order={order_id} cleared "
                    f"{levels_cleared} bid levels in {elapsed_us:.1f} us"
                )

            if qty > 0:
                resting = {
                    "id": order_id,
                    "price": price,
                    "qty": qty,
                    "sequence": sequence
                }
                heapq.heappush(sell_orders, (price, sequence, resting))

    if verbose:
        print("ChronosMatch matching engine stopped.")
