"""Local HTTP API and dashboard server for the ChronosMatch prototype.

Run with: python server.py
This is a local educational prototype, not a broker or live-exchange adapter.
"""
from __future__ import annotations

import json
import math
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from matching_engine.core import MatchingEngine
from order import Order
from ui_persistence.ledger import TradeLedger

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "chronosmatch.db"
HOST = "127.0.0.1"
PORT = 8000


class ChronosService:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.lock = threading.RLock()
        self.ledger = TradeLedger(db_path)
        self.engine = MatchingEngine(ledger=self.ledger)
        self.next_id = 1
        self.started_at_orders = 0
        self.running = False

    def state(self) -> dict:
        with self.lock:
            buys = sorted(
                [o for o in self.engine.order_book.buy_orders if o.remaining_quantity > 0],
                key=lambda o: (-o.price, o.timestamp),
            )
            sells = sorted(
                [o for o in self.engine.order_book.sell_orders if o.remaining_quantity > 0],
                key=lambda o: (o.price, o.timestamp),
            )
            recent = self.ledger.get_recent_trades(50)
            return {
                "ok": True,
                "running": self.running,
                "orders_processed": self.next_id - 1,
                "trades_matched": len(self.engine.trades),
                "order_book": {
                    "bids": [self._order_dict(o) for o in buys],
                    "asks": [self._order_dict(o) for o in sells],
                },
                "trades": recent,
                "analytics": self.ledger.get_trade_analytics(),
            }

    @staticmethod
    def _order_dict(order: Order) -> dict:
        return {
            "order_id": order.order_id,
            "symbol": order.symbol,
            "side": order.side,
            "price": order.price,
            "quantity": order.quantity,
            "remaining_quantity": order.remaining_quantity,
            "timestamp": order.timestamp,
        }

    def submit(self, payload: dict) -> dict:
        symbol = str(payload.get("symbol", "AAPL")).strip().upper()
        side = str(payload.get("side", "")).strip().upper()
        try:
            price = float(payload.get("price"))
            raw_quantity = payload.get("quantity")
            if isinstance(raw_quantity, bool):
                raise ValueError
            quantity = int(raw_quantity)
            if isinstance(raw_quantity, float) and not raw_quantity.is_integer():
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            raise ValueError("Price must be a number and quantity must be an integer.") from None
        if not symbol or len(symbol) > 16 or not symbol.isalnum():
            raise ValueError("Symbol must contain 1-16 letters or numbers.")
        if side not in ("BUY", "SELL"):
            raise ValueError("Side must be BUY or SELL.")
        if not math.isfinite(price) or price <= 0 or price > 1_000_000_000:
            raise ValueError("Price must be greater than 0 and within the supported limit.")
        if quantity < 1 or quantity > 1_000_000:
            raise ValueError("Quantity must be between 1 and 1,000,000.")

        with self.lock:
            order_id = str(self.next_id)
            self.next_id += 1
            order = Order(order_id, symbol, side, price, quantity)
            trades = self.engine.submit_order(order)
            return {
                "ok": True,
                "order": self._order_dict(order),
                "new_trades": trades,
                "state": self.state(),
            }

    def set_running(self, running: bool) -> dict:
        with self.lock:
            self.running = bool(running)
            return {"ok": True, "running": self.running}

    def reset(self) -> dict:
        with self.lock:
            # Keep the persistent ledger intact; reset only the live in-memory book/counters.
            self.engine = MatchingEngine(ledger=self.ledger)
            self.next_id = 1
            self.running = False
            return self.state()


SERVICE = ChronosService()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        print("[ChronosMatch] " + fmt % args)

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("Invalid Content-Length.") from None
        if length < 1 or length > 64_000:
            raise ValueError("Request body must be between 1 and 64,000 bytes.")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("Request body must be valid JSON.") from None
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object.")
        return payload

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json(200, {"ok": True, "service": "ChronosMatch local API"})
        elif path == "/api/state":
            self._send_json(200, SERVICE.state())
        else:
            super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/orders":
                self._send_json(200, SERVICE.submit(payload))
            elif path == "/api/engine":
                running = payload.get("running")
                if not isinstance(running, bool):
                    raise ValueError("'running' must be true or false.")
                self._send_json(200, SERVICE.set_running(running))
            elif path == "/api/reset":
                self._send_json(200, SERVICE.reset())
            else:
                self._send_json(404, {"ok": False, "error": "API endpoint not found."})
        except ValueError as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})
        except Exception as exc:
            self._send_json(500, {"ok": False, "error": "Internal server error.", "detail": str(exc)})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"ChronosMatch dashboard/API: http://{HOST}:{PORT}/ui/")
    print(f"API health check: http://{HOST}:{PORT}/api/health")
    print("Local prototype only; no broker/live-exchange connection.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping ChronosMatch server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
