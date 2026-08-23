# Operating context for fulfilment.py

This is the payment and stock path for a warehouse. It has been running for one week.

- One Python process, four worker threads, all running `run_forever()`.
- Arrival rate ~500 orders/hour, flat during business hours, near zero overnight.
- `payments.charge()` is an HTTPS call to a third-party payment provider. Normal
  latency ~2s. The provider publishes 99.9% availability and has had two incidents
  this year, 15 and 40 minutes, both returning 502s.
- `store.pool` is a Postgres connection pool, 10 connections, shared with the web tier.
- The process is restarted on every deploy. Deploys happen about twice a week, on
  weekday afternoons, by whoever merged last. There is no drain step; the orchestrator
  sends SIGTERM and then SIGKILL after 30 seconds.
- `submit()` is called from the web tier's checkout handler, synchronously, before it
  returns 200 to the customer's browser.
- The webhook endpoint receives payment status callbacks from the provider, roughly one
  per order, plus retries from the provider when it does not get a 200.
- Monitoring: process liveness, CPU, memory, and HTTP 5xx rate on the web tier. There
  are no metrics or alerts on job states, queue depth, or payment outcomes. The
  application log goes to stdout and is retained for 7 days.
- The team is three people. Nobody is on call overnight.
- Finance reconciles provider settlements against the orders table monthly.
