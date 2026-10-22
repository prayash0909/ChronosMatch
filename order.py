
from dataclasses import dataclass, field
from typing import Literal
from time import time_ns


@dataclass
class Order:
    order_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    price: float
    quantity: int
    timestamp: int = 0
    remaining_quantity: int = field(init=False)

    def __post_init__(self):
        if not self.order_id:
            raise ValueError("Order ID cannot be empty")

        if not self.symbol:
            raise ValueError("Symbol cannot be empty")

        self.symbol = self.symbol.upper()
        normalized_side = self.side.upper()
        if normalized_side == "BUY":
            self.side = "BUY"
        elif normalized_side == "SELL":
            self.side = "SELL"
        else:
            raise ValueError("Side must be BUY or SELL")

        if self.price <= 0:
            raise ValueError("Price must be positive")

        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

        if self.timestamp == 0:
            self.timestamp = time_ns()

        self.remaining_quantity = self.quantity

    @property
    def is_filled(self):
        return self.remaining_quantity == 0
