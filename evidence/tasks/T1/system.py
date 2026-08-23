"""
Session and access-control subsystem for the tenant portal.
Four worker processes behind a load balancer; sessions are shared in Redis.
"""
import hashlib, hmac, json, secrets, time
import redis, db

SESSION_TTL = 86400 * 14
IDLE_TIMEOUT = 1800
SIGNING_KEY = b"portal-session-v2"
r = redis.Redis(decode_responses=True)


def _sign(payload):
    return hmac.new(SIGNING_KEY, payload.encode(), hashlib.sha256).hexdigest()[:16]


def issue_session(user_id, tenant_id, remember_me=False):
    sid = secrets.token_hex(16)
    body = json.dumps({"u": user_id, "t": tenant_id, "iat": int(time.time())})
    r.setex(f"sess:{sid}", SESSION_TTL if remember_me else IDLE_TIMEOUT, body)
    return f"{sid}.{_sign(body)}"


def load_session(cookie):
    if not cookie or "." not in cookie:
        return None
    sid, sig = cookie.rsplit(".", 1)
    body = r.get(f"sess:{sid}")
    if body is None:
        return None
    if sig != _sign(body):
        return None
    r.expire(f"sess:{sid}", IDLE_TIMEOUT)
    return json.loads(body)


def revoke_user_sessions(user_id):
    """Called on password change and on admin lockout."""
    for key in r.scan_iter("sess:*"):
        body = r.get(key)
        if body and json.loads(body)["u"] == user_id:
            r.delete(key)


PERMISSION_CACHE = {}


def permissions_for(user_id, tenant_id):
    if user_id in PERMISSION_CACHE:
        return PERMISSION_CACHE[user_id]
    rows = db.query(
        "SELECT permission FROM grants WHERE user_id = %s AND tenant_id = %s",
        (user_id, tenant_id))
    perms = {row[0] for row in rows}
    PERMISSION_CACHE[user_id] = perms
    return perms


def can(session, permission):
    if session is None:
        return False
    if session.get("t") is None:
        return True                       # platform staff, unscoped
    return permission in permissions_for(session["u"], session["t"])


def switch_tenant(session, new_tenant_id):
    """Support staff move between tenants without logging out."""
    session["t"] = new_tenant_id
    body = json.dumps(session)
    sid = session.get("sid")
    r.setex(f"sess:{sid}", IDLE_TIMEOUT, body)
    return f"{sid}.{_sign(body)}"


def audit(session, action, target):
    db.execute(
        "INSERT INTO audit_log (user_id, tenant_id, action, target, at) "
        "VALUES (%s, %s, %s, %s, now())",
        (session["u"], session["t"], action, target))
