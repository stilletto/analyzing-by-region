# POOL — distinct verified claims about what happens when this system runs

Each entry is one mechanism at one place with one consequence. Verified against `system.py`
and `OPERATIONS.md`.

1. [remember-me-ttl-clobbered] MECHANISM: `issue_session` gives a remember-me session a 14-day TTL, but `remember_me` is never stored in the body and `load_session` runs `r.expire(key, IDLE_TIMEOUT)` unconditionally on every successful load. CONSEQUENCE: the first authenticated request after login rewrites the 14-day TTL down to 30 minutes, so the feature is inert for every user who ever comes back, and the re-logins it causes are 302/200s that no monitored signal separates from normal traffic.

2. [no-absolute-session-lifetime] MECHANISM: `iat` is written into the body at issue time and never read anywhere in the file, and the TTL refresh in `load_session` has no ceiling. CONSEQUENCE: a session touched at least once every 30 minutes never expires, so a cookie stolen in month one is still a valid credential in month twelve and nothing in this system can end it.

3. [idle-timeout-tracks-tab-not-user] MECHANISM: the TTL refresh fires on every authenticated request that reaches `load_session`, including background polling, prefetches and heartbeats. CONSEQUENCE: `IDLE_TIMEOUT` measures browser activity rather than human presence, so an unattended workstation with the portal open never times out while the control looks configured and correct in the source.

4. [abandoned-remember-me-keys-only-long-lived] MECHANISM: because any load collapses the TTL to 30 minutes, the only keys that retain the 14-day TTL are remember-me sessions nobody ever loaded again, and nothing subsequently touches them. CONSEQUENCE: the long-lived portion of the session keyspace consists entirely of sessions nobody is using, and those same keys are the coldest and therefore first in line for eviction.

5. [cookie-ttl-not-synchronized-with-redis-ttl] MECHANISM: `issue_session` returns a bare cookie string and discards the TTL decision, so whatever sets the browser cookie's lifetime has no access to the Redis TTL. CONSEQUENCE: the two clocks disagree with neither side logging it — a browser holding a 14-day cookie gets a silent bounce to login on every visit for two weeks after Redis collapsed the key to 30 minutes.

6. [signature-authenticates-server-side-data] MECHANISM: `_sign` covers only the body that `load_session` just fetched from Redis using the sid, and the sid itself is never signed. CONSEQUENCE: the tag is a consistency check between cookie and store rather than proof of issuance, so all real bearer security rests on the 128-bit `secrets.token_hex(16)` sid and strengthening the tag would change nothing.

7. [body-rewrite-silently-invalidates-cookies] MECHANISM: because the tag is computed over the stored body, any server-side rewrite of that body changes the expected tag for every cookie already issued against that key. CONSEQUENCE: the first time anyone writes a new field into a session body without re-issuing the cookie, affected users are logged out on their next request with no error, no log line and no distinguishing status code.

8. [identical-bodies-resurrect-stale-cookies] MECHANISM: `iat` is preserved across rewrites and `json.dumps` emits identical bytes for identical values, so returning a session to a previous state recreates a byte-identical body and therefore a byte-identical tag. CONSEQUENCE: a cookie invalidated by someone else's write becomes valid again later, so stale tabs and old cookies resurrect instead of failing permanently.

9. [signing-key-hardcoded-in-source] MECHANISM: `SIGNING_KEY = b"portal-session-v2"` is a literal in the module rather than a value from the environment or a secret store. CONSEQUENCE: the key sits in git history, every image layer, every clone and every backup, cannot be changed without a code deploy, and stays exposed after any future rotation because the history keeps it.

10. [key-rotation-is-a-rolling-logout] MECHANISM: the cookie is `sid.tag` with no key id and `load_session` verifies against exactly one key, while deploys are rolling with no sticky sessions. CONSEQUENCE: changing `SIGNING_KEY` invalidates every stored body at once and, for the whole rollout window, round-robin sends each user alternately to old-key and new-key processes so nobody can stay logged in until the roll completes.

11. [redis-read-plus-source-mints-cookies] MECHANISM: a cookie is nothing but a sid plus an HMAC of the stored body, so anyone who can read Redis learns both halves of the input while the key comes from the source file. CONSEQUENCE: repository access combined with any read access to Redis — a `redis-cli` session, an RDB file, a staging restore — is enough to mint a valid cookie for any live session, including a staff one.

12. [sid-unvalidated-as-key-name] MECHANISM: `load_session` splits the cookie on the last dot and interpolates the result straight into `f"sess:{sid}"` with no length, charset or format check. CONSEQUENCE: any client can aim a lookup at an arbitrary key under the `sess:` prefix, which is what makes the accidentally created `sess:None` key reachable from a hand-written cookie.

13. [load-session-failures-indistinguishable] MECHANISM: `load_session` has three `return None` paths and no logging or counters, so a missing key and a failed signature produce the same result. CONSEQUENCE: expired, evicted, forged, corrupt and never-existed sessions collapse into one observable event — a bounce to login — and no signal anywhere separates a forgery attempt from an ordinary expiry.

14. [expire-on-every-read-write-amplification] MECHANISM: every authenticated request costs a `GET` plus an `EXPIRE`, and `EXPIRE` is a write command. CONSEQUENCE: the hot path doubles its round trips against a single-threaded Redis and turns a read-mostly session store into a write workload that changes no data.

15. [revoke-scans-whole-keyspace-inline] MECHANISM: `revoke_user_sessions` enumerates with `scan_iter("sess:*")` (redis-py's default COUNT of 10, with MATCH applied after iteration) and issues one un-pipelined `GET` per key, inline in the request that triggered it. CONSEQUENCE: cost is proportional to the total number of keys on the node rather than to that user's sessions, and one of only four worker processes is blocked for the seconds it takes.

16. [revoke-triggered-by-unprivileged-user-action] MECHANISM: the same function runs on every self-service password change, which users perform at will and which nothing here rate-limits. CONSEQUENCE: an ordinary unprivileged action fires a full keyspace sweep, so a forced-reset campaign or breach notification puts many concurrent sweeps on one single-threaded Redis and degrades the portal for everyone.

17. [revoke-latency-visible-but-unattributable] MECHANISM: no individual command in the sweep is slow — the cost is thousands of fast round trips, which appear in no per-command instrumentation or slowlog, and nothing emits a revocation metric. CONSEQUENCE: the one monitored signal it moves, p99 latency, arrives with no correlating cause, so operators scale Redis or blame the database while the round-trip count that actually causes it is never named.

18. [revoke-scan-race-misses-new-sessions] MECHANISM: `SCAN` guarantees only that keys present for the entire iteration are returned, so a key created mid-sweep may never be visited. CONSEQUENCE: an account that re-authenticates while its lockout sweep is running can keep a session the sweep was meant to kill, and the function still completes cleanly.

19. [revoke-reports-nothing] MECHANISM: the function returns no value, counts nothing and logs nothing, and there is no alerting on session count. CONSEQUENCE: "did the lockout work?" is unanswerable from anything the system produces, so a partial, raced or entirely inert revocation is indistinguishable from a complete one.

20. [revoke-type-mismatch-silent-noop] MECHANISM: the match is `json.loads(body)["u"] == user_id`, a strict comparison with no normalization across a JSON round trip. CONSEQUENCE: if a caller supplies `user_id` as a string where the body holds an integer — an admin console form, a URL segment, a CSV of accounts to lock — nothing matches, nothing is deleted, no exception is raised, and the lockout reports success.

21. [revoke-aborts-on-malformed-body] MECHANISM: `json.loads(body)["u"]` is unguarded and the `sess:*` pattern is greedy over an unnamespaced prefix. CONSEQUENCE: one value under that prefix that is not JSON carrying a `"u"` field raises mid-iteration, leaving revocation partially applied with some sessions deleted and the rest untouched.

22. [revoke-logs-out-the-caller] MECHANISM: the sweep deletes every key whose body carries the target user id, with no exclusion for the session making the request. CONSEQUENCE: a user who changes their own password is logged out of the session they are currently using, immediately after being told the change succeeded.

23. [revoke-is-point-in-time-only] MECHANISM: revocation is a delete of the keys that exist at that instant, while `load_session` consults nothing but Redis and `issue_session` gates on nothing at all. CONSEQUENCE: nothing in this module gives a lockout any durability — the moment the sweep finishes, an actor still holding valid credentials can obtain a fresh session.

24. [no-user-to-session-index] MECHANISM: nothing maps a user to their sessions; the full-keyspace scan is the index, and `iat` is only reachable inside an opaque body. CONSEQUENCE: there is no way to list a user's sessions, revoke a single device, or tell an incident responder when any of a user's sessions began.

25. [revoke-resets-session-lru] MECHANISM: `SCAN` does not touch an object's LRU clock but the `GET` issued for every matching key does, so each sweep marks every session key on the instance as freshly used. CONSEQUENCE: after each password change the LRU ordering among sessions is flattened and eviction pressure shifts onto whatever else shares the node, coupling password-change activity to the hit rate of unrelated keys.

26. [allkeys-lru-evicts-live-sessions] MECHANISM: the node runs `allkeys-lru`, so session keys — the only copy of login state anywhere — are eviction candidates on equal terms with any other data on the node, and writes evict rather than returning OOM. CONSEQUENCE: under memory pressure users are logged out mid-task with no exception and no error, and the application cannot tell an evicted session from an expired one.

27. [eviction-invisible-to-monitoring] MECHANISM: monitoring covers Redis memory and hit rate but not evicted keys or session count, and an LRU node sitting at `maxmemory` is its normal steady state. CONSEQUENCE: the memory graph reads as healthy precisely while sessions are being destroyed, so a wave of logouts reaches operators only as support tickets, days later.

28. [redis-single-node-total-session-loss] MECHANISM: sessions live only on one Redis node, with no replica and no second store. CONSEQUENCE: any event that loses that keyspace — a restart, a host patch, an OOM kill — logs out all ~4,000 users and all 12 staff simultaneously and dumps a re-login stampede onto the auth path.

29. [redis-down-500s-not-logouts] MECHANISM: no Redis call in the file is wrapped in `try`, and `load_session` runs on every authenticated request. CONSEQUENCE: a Redis outage propagates `ConnectionError` out of `r.get` as an HTTP 500 on every authenticated request rather than a graceful bounce to login — the one failure here that the monitored status rates catch immediately.

30. [no-socket-timeout-hangs-fleet] MECHANISM: `redis.Redis(decode_responses=True)` sets no `socket_timeout`, `socket_connect_timeout` or `health_check_interval`. CONSEQUENCE: a slow or hung Redis parks every worker in `recv()` with no deadline, so all four processes stop answering while HTTP status rates and p99 — both computed from completed requests — stay clean.

31. [redis-client-all-defaults] MECHANISM: the client is built with every default — db 0, default host and port, no auth, no TLS, no namespace beyond the `sess:` prefix. CONSEQUENCE: the store holding all authentication state has no credential or transport protection of its own and shares one keyspace and one eviction pool with anything else later added to that node.

32. [switch-writes-to-sess-none] MECHANISM: `load_session` returns `json.loads(body)`, which contains only `u`, `t` and `iat`, so `session.get("sid")` inside `switch_tenant` is always `None`. CONSEQUENCE: every tenant switch in the fleet writes to the single literal key `sess:None` and returns the cookie `"None.<tag>"`, which then loads successfully and therefore looks correct to the one engineer who tests it alone.

33. [shared-slot-mutual-logout] MECHANISM: all twelve support staff switching many times a day converge on that one key, last writer wins, and each write changes the body the tag is computed over. CONSEQUENCE: every switch invalidates the cookie of every other staffer currently riding the key, producing constant apparently-random logouts that a single tester can never reproduce because the collision requires two people.

34. [signature-turns-confusion-into-logout] MECHANISM: `load_session` rejects any cookie whose tag does not match the body currently stored at the key it names. CONSEQUENCE: the shared `sess:None` slot produces logouts instead of one staffer loading another staffer's identity, so the only thing standing between a shared session key and cross-user impersonation is the tag comparison.

35. [switch-not-durable-real-key-stale] MECHANISM: the switch mutates `session["t"]` in memory and persists to `sess:None`, never updating or deleting the real `sess:<sid>` key, whose body still carries the old tenant. CONSEQUENCE: unless the client adopts the returned cookie the switch applies only for the current request and silently reverts, and the pre-switch session stays valid for its full idle window so the staffer can be live in two tenant contexts at once depending on which cookie is sent.

36. [sess-none-permanent-and-addressable] MECHANISM: `sess:None` is rewritten and TTL-refreshed continuously by a dozen staff, and its name is a fixed, guessable string reachable through the unvalidated sid. CONSEQUENCE: a permanently live session key carrying a real staff identity sits at a well-known address any browser can aim a cookie at, and it is the one session key that will never expire or be evicted.

37. [switch-has-no-authorization-check] MECHANISM: `switch_tenant` never verifies that the caller is platform staff, never validates `new_tenant_id` against anything the user may access, and never calls `can()`. CONSEQUENCE: the entire control rests on whatever route sits in front of it, and if that route is ungated any of the ~4,000 users can set their own session's tenant to an enumerable id belonging to someone else.

38. [switch-to-null-tenant-is-escalation] MECHANISM: `switch_tenant(session, None)` writes `t = None`, and `can()` returns `True` for every permission whenever `t is None`. CONSEQUENCE: one request with an omitted or empty tenant parameter converts an ordinary tenant user into an unscoped session that passes every permission check in the system.

39. [switch-is-never-audited] MECHANISM: `switch_tenant` writes no audit row and its only durable trace, `sess:None`, is overwritten by the next switch, so the tenant a staffer is acting in exists only at the moment of the action. CONSEQUENCE: the NULL tenant fields in `audit_log` can never be reconstructed or backfilled, so the attribution debt accrues every day the system runs and is unpayable.

40. [permission-cache-keyed-by-user-only] MECHANISM: `permissions_for` scopes its SQL by `user_id AND tenant_id` but both reads and writes `PERMISSION_CACHE` under `user_id` alone, leaving `tenant_id` dead after the first call. CONSEQUENCE: the first tenant a user is evaluated against in a process fixes that user's permission set for every other tenant for the life of that process.

41. [wrong-direction-of-bleed-is-silent] MECHANISM: the cached set can be smaller or larger than the real grants for the current tenant, and there is no instrumentation on permission checks. CONSEQUENCE: the harmless direction produces a denial the user reports within minutes while the dangerous direction is an ordinary HTTP 200 that nothing counts, so only the safe half of the bug ever generates evidence.

42. [permission-cache-never-invalidated] MECHANISM: the cache has no TTL, no size bound and no invalidation hook, and nothing on the grant-editing path touches it, so only process death clears it. CONSEQUENCE: an admin's role edit is not live at once as expected but only when a process restarts — up to roughly 24 hours given daily rolling deploys.

43. [deploy-cadence-is-the-invalidation] MECHANISM: the ~24-hour staleness bound is an accident of the rolling deploy schedule rather than a property of the code, and nothing records that dependency. CONSEQUENCE: any pause in deploys — a holiday freeze, an incident freeze, a move to weekly releases — silently extends permission staleness to weeks, so grant removals stop taking effect at all during exactly the period when nobody expects behaviour to change.

44. [per-process-caches-make-authorization-nondeterministic] MECHANISM: `PERMISSION_CACHE` is a module global held independently by four processes behind a round-robin balancer with no sticky sessions. CONSEQUENCE: the same user's consecutive requests get different permission answers, so a page renders a control from one process and 403s when the API call lands on another, which is triaged as a flaky front end rather than an authorization defect.

45. [logout-does-not-reset-permissions] MECHANISM: the cache is keyed by user and outlives the session entirely, and nothing in the session lifecycle — including `revoke_user_sessions` — touches it. CONSEQUENCE: "log out and back in" and even a full session revocation leave the stale permission set intact, so the obvious remedy does nothing and appears to work only when a deploy happens to intervene.

46. [empty-permission-set-is-cached] MECHANISM: `perms` is stored even when the query returns no rows. CONSEQUENCE: a user evaluated before their grants exist — a new onboarding, or any tenant they hold no rows in — has an empty set pinned under their user id for the life of the process, and only a restart clears it.

47. [switching-strips-support-permissions] MECHANISM: a support account with no `grants` rows in the tenant it switches into caches the empty set under its user id, while remaining unscoped bypasses `permissions_for` entirely through the `t is None` branch. CONSEQUENCE: switching costs a staffer every permission until the next restart while staying unscoped grants them everything, so the tool punishes the compliant behaviour.

48. [support-abandons-tenant-switching] MECHANISM: for twelve people making many switches a day, switching produces logouts and permission loss while unscoped work is smooth and unrestricted. CONSEQUENCE: support settles into operating permanently unscoped as a habit rather than a configuration change, which nothing logs, nothing alerts on and no dashboard can show.

49. [null-tenant-means-every-permission] MECHANISM: `can()` returns `True` whenever `session.get("t") is None`, without consulting the permission argument, any staff flag, or the database. CONSEQUENCE: the twelve support accounts whose resting state is `t = null` hold unconditional authority across all 300 tenants, and not one of their actions passes through a real permission check.

50. [missing-tenant-fails-open] MECHANISM: `.get("t")` cannot distinguish a null tenant from an absent one, and `issue_session` performs no validation of `tenant_id`. CONSEQUENCE: any path that yields a session without a resolved tenant — an SSO or invite flow, a lookup returning None, a hand-built or partial session dict — mints a platform superuser instead of failing, and the result is invisible because null tenants are already normal.

51. [future-permissions-preapproved] MECHANISM: the unscoped branch returns `True` before the permission string is examined at all. CONSEQUENCE: every privileged capability added over the year is fully open to unscoped sessions from the day it merges, and no code review catches it because the call site reads as a correct permission check.

52. [denials-are-never-recorded] MECHANISM: `can()` returns `False` silently, never logs, never calls `audit()`, and there is no alerting on permission checks. CONSEQUENCE: no record exists anywhere of an attempted-and-blocked privileged action, so an investigation can see only what succeeded and never an attacker's probing.

53. [cached-set-shared-by-reference] MECHANISM: `permissions_for` stores and returns the same mutable set object rather than a copy. CONSEQUENCE: the first caller that mutates the returned set — a temporary elevation, an implied permission, a test helper — permanently escalates that user on that process until the next restart, with no trace.

54. [audit-writes-null-tenant-for-privileged-actions] MECHANISM: `audit()` copies `session["t"]` straight into `audit_log.tenant_id`, and `t` is null for exactly the unscoped sessions that `can()` grants unlimited authority. CONSEQUENCE: the requirement that every privileged action be attributable to a person and a tenant fails precisely for the highest-authority actions in the system, silently, because nothing alerts on audit-log writes.

55. [breach-cannot-be-scoped] MECHANISM: with the tenant absent from every unscoped staff action, no data anywhere ties a support account's activity to particular tenants. CONSEQUENCE: after a compromise of one of the twelve staff accounts, responders cannot show which of the 300 tenants were touched or prove that any given tenant was not, turning a scoped incident into an unscopeable one.

56. [can-and-audit-disagree-on-missing-tenant] MECHANISM: `can()` reads the tenant with `.get("t")` while `audit()` reads it with `session["t"]`. CONSEQUENCE: the same malformed session that `can()` treats as unconditional allow makes `audit()` raise `KeyError`, so the request with the most authority is the one that cannot be logged, surfacing as an ordinary 5xx.

57. [audit-not-transactional] MECHANISM: the audit INSERT is a separate `db.execute` with no shared transaction with the action it records. CONSEQUENCE: actions commit with no audit row and audit rows survive failed actions, and the divergence is never reconciled because nothing alerts on audit-log writes.

58. [audit-is-opt-in] MECHANISM: nothing couples `can()` to `audit()` — each call site must remember the helper, with no wrapper or decorator enforcing it. CONSEQUENCE: new endpoints ship performing privileged actions with no audit row at all, and neither the omission nor a drop in audit volume is detectable given the stated monitoring.

59. [audit-row-lacks-correlation-fields] MECHANISM: the row carries only user id, tenant id, action, target and timestamp — no session id, IP, request id, permission consulted, or outcome. CONSEQUENCE: an investigator cannot group actions into a session, cannot join to the session store (which has no index either), and cannot tell an attempted action from a completed one.

60. [audit-tenant-is-self-asserted] MECHANISM: the tenant written to the log is the same unvalidated, caller-supplied `session["t"]` that `switch_tenant` set and that decides the authorization outcome. CONSEQUENCE: a caller chooses which tenant their action is filed under, so the attribution control and the access control are bypassed by the same single field.

61. [bled-action-produces-legitimate-looking-row] MECHANISM: `audit()` records the session's asserted tenant, never the tenant whose grants actually decided the outcome nor the tenant of the object touched. CONSEQUENCE: an action authorized by the wrong tenant's cached permissions writes a perfectly well-formed row, so cross-tenant exposure leaves no trace distinguishing it from routine work.

62. [reconciliation-implicates-innocent-actor] MECHANISM: reconciling `audit_log` against `grants` surfaces rows where the actor held no grant in the recorded tenant, produced by stale caches and cross-tenant bleed. CONSEQUENCE: the log asserts something false rather than merely omitting something true, and the natural readings — grants tampering, insider abuse, a compromised account — all point at a person long before anyone reaches "a dict was keyed by user instead of by user and tenant".

63. [no-acting-as-marker] MECHANISM: customer users and vendor staff share one identity namespace in `audit_log`, with no on-behalf-of or acting-as column. CONSEQUENCE: even a correctly attributed staff action inside a tenant is indistinguishable from an action by that tenant's own employee.

64. [one-symptom-three-mechanisms] MECHANISM: remember-me demotion, `sess:None` collisions, and eviction or a Redis restart all present identically as a bounce to the login page with no distinguishing status code or log line. CONSEQUENCE: they are triaged as a single "random logout" ticket, so a correct fix to any one of them fails to move ticket volume, is judged ineffective, and is at risk of being reverted.

65. [restarting-to-reproduce-destroys-evidence] MECHANISM: the only thing that clears `PERMISSION_CACHE` is process death, and the standard way to investigate or reproduce is to restart or redeploy. CONSEQUENCE: authorization is most wrong the longer a process has been up and correct immediately after a restart, so every reproduction attempt cures the symptom and the ticket closes as not-reproducible.

66. [idle-timeout-constant-is-overloaded] MECHANISM: `IDLE_TIMEOUT` is simultaneously the non-remember-me session lifetime, the refresh window on every load, and the TTL that `switch_tenant` writes. CONSEQUENCE: the cheapest-looking fix for the remember-me complaints — raising that one constant — turns every ordinary session into a multi-day session, multiplying live keys, the cost of every revocation sweep, and the population of simultaneously valid credentials.

67. [async-revoke-fix-defeats-immediate-lockout] MECHANISM: the revocation sweep's p99 spike is the only monitored signal the session layer produces, and the obvious remedy is to move revocation into a background job. CONSEQUENCE: that fix removes the visible symptom while keeping the O(keyspace) cost and makes revocation queue-delayed, directly against the operational expectation that lockout takes effect immediately.

68. [sid-fix-unmasks-cross-tenant-bleed] MECHANISM: putting a real sid into the session makes tenant switches durable while `permissions_for` still caches by user id alone. CONSEQUENCE: the repair ends the logout storm that was accidentally limiting how often staff switched, turning cross-tenant permission bleed from rare into routine and removing both signals — the logout and the empty permission set — that the bug ever produced.

69. [closing-fail-open-locks-out-support] MECHANISM: removing the `t is None` short-circuit routes all twelve staff through `permissions_for` for the first time, against a cache keyed by user and `grants` rows they never needed to have. CONSEQUENCE: the correct security fix locks the entire support team out fleet-wide on the day it ships unless the cache key and their grants are corrected first, which buys the fail-open another year.

70. [correct-cache-fix-reads-as-regression] MECHANISM: the permanent cache currently absorbs essentially every grant read, so keying it correctly with real invalidation both withdraws permissions users have been coasting on and restores the database query volume. CONSEQUENCE: the fix arrives as a wave of "I lost access" tickets plus a step change in DB load and p99, all three of which are the fix working correctly and all three of which read as a regression on the only instruments the team has.
