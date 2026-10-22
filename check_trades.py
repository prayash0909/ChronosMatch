
from ui_persistence.ledger import TradeLedger

ledger = TradeLedger()

print("\n===== LATEST CHRONOSMATCH TRADES =====")

for trade in ledger.get_recent_trades(limit=10):
    print(trade)
