
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class TradeLedger:
    @contextmanager
    def _connection(self):
        """Yield a SQLite connection and always close it, including on Windows."""
        connection = sqlite3.connect(self.db_path)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def __init__(self, db_path="chronosmatch.db"):
        self.db_path = Path(db_path)

        with self._connection() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    buy_order_id INTEGER NOT NULL,
                    sell_order_id INTEGER NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def record_trade(
        self, buy_order_id, sell_order_id, price, quantity
    ):
        with self._connection() as connection:
            connection.execute("""
                INSERT INTO trades (
                    buy_order_id, sell_order_id, price, quantity
                )
                VALUES (?, ?, ?, ?)
            """, (buy_order_id, sell_order_id, price, quantity))

    def get_recent_trades(self, limit=10):
        with self._connection() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute("""
                SELECT * FROM trades
                ORDER BY id DESC
                LIMIT ?
            """, (limit,)).fetchall()

            return [dict(row) for row in rows]

    def get_trade_analytics(self):
        with self._connection() as connection:
            result = connection.execute("""
                SELECT
                    COUNT(*) AS total_trades,
                    COALESCE(SUM(quantity), 0) AS total_quantity,
                    COALESCE(AVG(price), 0) AS average_price
                FROM trades
            """).fetchone()

            return {
                "total_trades": result[0],
                "total_quantity": result[1],
                "average_price": round(result[2], 2)
            }



if __name__ == "__main__":
    ledger = TradeLedger()

    ledger.record_trade(
        buy_order_id=2003,
        sell_order_id=2001,
        price=100.0,
        quantity=3
    )

    print("Recent trades:")
    for trade in ledger.get_recent_trades():
        print(trade)
