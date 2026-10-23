
import sqlite3

connection = sqlite3.connect("chronosmatch.db")

try:
    result = connection.execute("""
        SELECT COUNT(*), COALESCE(SUM(quantity), 0)
        FROM trades
        WHERE buy_order_id LIKE 'B%'
          AND sell_order_id LIKE 'S%'
    """).fetchone()

    print("Matching trade records:", result[0])
    print("Total traded quantity:", result[1])

finally:
    connection.close()
