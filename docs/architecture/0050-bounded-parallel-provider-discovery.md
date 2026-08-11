# ADR 0050: Bounded parallel provider discovery

- Status: Accepted
- Date: 2026-08-12

## Context

Direct and aggregator coverage has expanded enough that sequential provider calls make search time
grow with every source. A single slow provider must not hold back jobs already returned by healthy
sources, and concurrency must not create an unbounded thread pool.

## Decision

Run provider searches through one process-local executor owned by the discovery service, capped at
eight threads. Preserve provider registry order when collecting completed results. Stop waiting at
45 seconds, cancel work that has not started, and report unfinished sources as timed out while
retaining all completed results.

Emit one privacy-bounded structured latency record for each observed provider outcome. Explicitly
close the executor during API and worker shutdown. Running HTTP calls cannot be forcefully killed;
they finish under adapter-level request timeouts after the search response stops waiting.

## Consequences

- Normal search latency approaches the slowest completed source rather than the sum of all sources.
- Thread concurrency remains bounded per API or worker process.
- Slow sources do not erase timely results from other providers.
- A future load test can tune worker count and budget without changing provider adapters.
