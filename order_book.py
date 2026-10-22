
class OrderBook:
    def __init__(self):
        self.buy_orders = []
        self.sell_orders = []

    def add_order(self, order):
        if order.side == "BUY":
            self.buy_orders.append(order)
            self.buy_orders.sort(
                key=lambda o: (-o.price, o.timestamp)
            )
        elif order.side == "SELL":
            self.sell_orders.append(order)
            self.sell_orders.sort(
                key=lambda o: (o.price, o.timestamp)
            )
        else:
            raise ValueError("Side must be BUY or SELL")

    def best_opposite(self, symbol, side):
        symbol = symbol.upper()

        if side == "BUY":
            candidates = [
                o for o in self.sell_orders
                if o.symbol == symbol
                and o.remaining_quantity > 0
            ]
            return min(
                candidates,
                key=lambda o: (o.price, o.timestamp),
                default=None
            )

        elif side == "SELL":
            candidates = [
                o for o in self.buy_orders
                if o.symbol == symbol
                and o.remaining_quantity > 0
            ]
            return min(
                candidates,
                key=lambda o: (-o.price, o.timestamp),
                default=None
            )

        raise ValueError("Side must be BUY or SELL")

    def remove_order(self, order):
        orders = (
            self.buy_orders
            if order.side == "BUY"
            else self.sell_orders
        )

        if order in orders:
            orders.remove(order)
