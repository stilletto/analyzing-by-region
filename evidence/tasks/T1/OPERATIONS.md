# Operating context

- Four identical web processes behind a round-robin load balancer. No sticky sessions.
- Redis is a single node, no replica, `maxmemory 512mb`, eviction policy `allkeys-lru`.
- ~4,000 daily active users across ~300 tenants. Support staff (about 12 people) use
  switch_tenant many times a day and have `t` set to null when not switched.
- Passwords can be changed by users at will; admin lockout is used a few times a month,
  usually during a security incident, and is expected to take effect immediately.
- Grants change when an admin edits a role. Admins expect the change to be live at once.
- Deploys are rolling, one process at a time, about daily.
- Monitoring: HTTP status rates, p99 latency, Redis memory and hit rate. No alerting on
  session count, permission checks, or audit-log writes.
- There is a compliance requirement that every privileged action is attributable to a
  person and a tenant.
