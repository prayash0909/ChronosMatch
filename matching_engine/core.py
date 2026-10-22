from order_book import OrderBook
from ui_persistence.ledger import TradeLedger


class MatchingEngine:
    def __init__(self, ledger=None):
        self.order_book = OrderBook()
        self.trades = []
        self.ledger = ledger or TradeLedger()

    def submit_order(self, order):
        new_trades = []

        while order.remaining_quantity > 0:
            opposite = self.order_book.best_opposite(
                order.symbol, order.side
            )

            if opposite is None:
                break

            if order.side == "BUY":
                if order.price < opposite.price:
                    break
            else:
                if order.price > opposite.price:
                    break

            quantity = min(
                order.remaining_quantity,
                opposite.remaining_quantity
            )

            trade = {
                "symbol": order.symbol,
                "price": opposite.price,
                "quantity": quantity,
                "incoming_order_id": order.order_id,
                "matched_order_id": opposite.order_id,
            }

            if order.side == "BUY":
                buy_id = order.order_id
                sell_id = opposite.order_id
            else:
                buy_id = opposite.order_id
                sell_id = order.order_id

            self.ledger.record_trade(
                buy_order_id=buy_id,
                sell_order_id=sell_id,
                price=opposite.price,
                quantity=quantity
            )

            order.remaining_quantity -= quantity
            opposite.remaining_quantity -= quantity

            self.trades.append(trade)
            new_trades.append(trade)

            if opposite.is_filled:
                self.order_book.remove_order(opposite)

        if order.remaining_quantity > 0:
            self.order_book.add_order(order)

        return new_trades
