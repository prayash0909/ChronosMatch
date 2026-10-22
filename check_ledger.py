
from ui_persistence.ledger import TradeLedger

ledger = TradeLedger()

print("Recent trades:")
for trade in ledger.get_recent_trades():
    print(trade)

print("\nTrade analytics:")
print(ledger.get_trade_analytics())
