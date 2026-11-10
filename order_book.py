
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
                if o.symbol == symbol and o.remaining_quantity > 0
            ]
            return min(
                candidates,
                key=lambda o: (o.price, o.timestamp),
                default=None
            )

        if side == "SELL":
            candidates = [
                o for o in self.buy_orders
                if o.symbol == symbol and o.remaining_quantity > 0
            ]
            return min(
                candidates,
                key=lambda o: (-o.price, o.timestamp),
                default=None
            )

        raise ValueError("Side must be BUY or SELL")

    def remove_order(self, order):
        orders = (
            self.buy_orders if order.side == "BUY"
            else self.sell_orders
        )
        if order in orders:
            orders.remove(order)

    def cancel_order(self, order_id):
        for orders in (self.buy_orders, self.sell_orders):
            for order in orders:
                if order.order_id == order_id:
                    orders.remove(order)
                    return True
        return False


class MultiSymbolOrderBook:
    """Maintains an independent order book for every trading symbol."""

    def __init__(self):
        self.books = {}

    def get_book(self, symbol):
        symbol = symbol.upper()
        if not symbol:
            raise ValueError("Symbol cannot be empty")
        if symbol not in self.books:
            self.books[symbol] = OrderBook()
        return self.books[symbol]

    @property
    def symbols(self):
        return list(self.books.keys())

    @property
    def buy_orders(self):
        return [
            order
            for book in self.books.values()
            for order in book.buy_orders
        ]

    @property
    def sell_orders(self):
        return [
            order
            for book in self.books.values()
            for order in book.sell_orders
        ]

    def add_order(self, order):
        self.get_book(order.symbol).add_order(order)

    def best_opposite(self, symbol, side):
        book = self.books.get(symbol.upper())
        if book is None:
            return None
        return book.best_opposite(symbol, side)

    def remove_order(self, order):
        book = self.books.get(order.symbol.upper())
        if book is not None:
            book.remove_order(order)

    def cancel_order(self, order_id, symbol=None):
        if symbol is not None:
            book = self.books.get(symbol.upper())
            return book.cancel_order(order_id) if book else False

        for book in self.books.values():
            if book.cancel_order(order_id):
                return True
        return False
