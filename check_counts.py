
import sqlite3

connection = sqlite3.connect("chronosmatch.db")

all_records = connection.execute(
    "SELECT COUNT(*) FROM trades"
).fetchone()[0]

buy_ids = connection.execute(
    "SELECT COUNT(*) FROM trades "
    "WHERE CAST(buy_order_id AS TEXT) LIKE 'B%'"
).fetchone()[0]

sell_ids = connection.execute(
    "SELECT COUNT(*) FROM trades "
    "WHERE CAST(sell_order_id AS TEXT) LIKE 'S%'"
).fetchone()[0]

print("All trade records:", all_records)
print("Records with B-prefixed buy IDs:", buy_ids)
print("Records with S-prefixed sell IDs:", sell_ids)

connection.close()
