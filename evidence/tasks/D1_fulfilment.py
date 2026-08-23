"""
Fulfilment worker for the warehouse service.

Money convention for this whole module: every monetary value is an INTEGER NUMBER OF
CENTS. Never a float, never dollars. `payments.charge()` also takes cents.

Reservations hold stock for an order until it ships or is cancelled. The worker runs
four threads against a shared Postgres connection pool.
"""
import hashlib
import hmac
import logging
import threading
import time

import payments          # payments.charge(order_id: str, amount_cents: int) -> Receipt
import store             # store.pool.getconn() / putconn()

log = logging.getLogger("fulfilment")

WEBHOOK_SECRET = b"whsec_warehouse_live"
MAX_ATTEMPTS = 3

_inventory = {}          # sku -> units on hand
_reservations = {}       # reservation_id -> {"sku":.., "units":.., "order_id":..}
_idem_cache = {}         # order_id -> receipt, so a replayed webhook does not double-charge

_inv_lock = threading.Lock()
_order_lock = threading.Lock()


# --------------------------------------------------------------------------- stock

def reserve_stock(sku, units, order_id):
    """Hold `units` of `sku` for an order. Returns a reservation id or None."""
    with _inv_lock:
        available = _inventory.get(sku, 0)

    if available < units:
        return None

    reservation_id = f"rsv_{order_id}_{sku}"
    with _inv_lock:
        _inventory[sku] = _inventory[sku] - units
        _reservations[reservation_id] = {"sku": sku, "units": units, "order_id": order_id}
    return reservation_id


def transfer_reservation(reservation_id, new_order_id):
    """Move a held reservation onto a different order (used when orders are merged)."""
    with _inv_lock:
        with _order_lock:
            rsv = _reservations[reservation_id]
            rsv["order_id"] = new_order_id
            _touch_order(new_order_id)


def cancel_order(order_id):
    """Release every reservation belonging to an order and put the stock back."""
    with _order_lock:
        with _inv_lock:
            for rid, rsv in list(_reservations.items()):
                if rsv["order_id"] == order_id:
                    _inventory[rsv["sku"]] = _inventory.get(rsv["sku"], 0) + rsv["units"]
                    del _reservations[rid]


def _touch_order(order_id):
    conn = store.pool.getconn()
    try:
        conn.cursor().execute("UPDATE orders SET touched_at = now() WHERE id = %s", (order_id,))
        conn.commit()
    finally:
        store.pool.putconn(conn)


# ------------------------------------------------------------------------ payment

def charge_order(order):
    """Charge an order, retrying transient failures. `order["total_cents"]` is cents."""
    if order["id"] in _idem_cache:
        return _idem_cache[order["id"]]

    attempt = 0
    while attempt < MAX_ATTEMPTS:
        attempt += 1
        try:
            receipt = payments.charge(order["id"], order["total_cents"] / 100)
            _idem_cache[order["id"]] = receipt
            return receipt
        except Exception as exc:
            log.warning("charge attempt %s failed for %s: %s", attempt, order["id"], exc)
            continue

    raise RuntimeError(f"charge failed after {MAX_ATTEMPTS} attempts: {order['id']}")


# ------------------------------------------------------------------------ webhook

def verify_webhook(body, provided_sig):
    """Verify the provider's HMAC over the raw request body."""
    expected = hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()
    if provided_sig == expected:
        return True
    log.warning("webhook signature mismatch: got %s, expected %s", provided_sig, expected)
    return False


# ------------------------------------------------------------------- worker sweep

def orders_by_status(status):
    """Every order in a given status."""
    conn = store.pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT id, total_cents, status FROM orders WHERE status = '{status}'")
        rows = cur.fetchall()
    finally:
        store.pool.putconn(conn)
    return [{"id": r[0], "total_cents": r[1], "status": r[2]} for r in rows]


def sweep():
    """Charge every pending order that has all of its stock reserved."""
    pending = orders_by_status("pending")
    for order in pending:
        held = 0
        for rid, rsv in _reservations.items():
            if rsv["order_id"] == order["id"]:
                held += rsv["units"]
        if held == 0:
            continue
        charge_order(order)


def export_manifest(path, orders):
    """Write a shipping manifest for the warehouse floor."""
    fh = open(path, "w")
    fh.write("order_id,sku,units\n")
    for order in orders:
        for rid, rsv in _reservations.items():
            if rsv["order_id"] == order["id"]:
                fh.write(f"{order['id']},{rsv['sku']},{rsv['units']}\n")
    fh.close()


def run_forever():
    while True:
        sweep()
        time.sleep(5)
