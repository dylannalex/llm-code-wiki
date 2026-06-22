# Worked example — a decision page

> **This is a format reference, not wiki content.** It lives in `docs/` (outside the `wiki/`
> vault) precisely so the agent never mistakes it for a real decision. Use it as a template for
> what a `wiki/decisions/<slug>.md` page should look like. Notice: the frontmatter cites its
> sources (a code file with a `sha256`, a web article and a session with `pulled` dates), the
> body **leads with the decision**, and it records the **rejected alternatives and why** — that
> "why" is the value a decision page preserves.

```markdown
---
title: Choose a message-queue approach
scope: ours
type: decision
sources:
  - source_type: repository
    path: my-service/src/queue/consumer.ts
    sha256: <run scripts/hash.sh on the file and paste the hash here>
  - source_type: web
    path: https://example.com/some-reference-article
    pulled: 2025-01-01
  - source_type: ai-agent-session
    path: raw/ai-agent-sessions/2025-01-01-queue-design.md
    pulled: 2025-01-01
status: current
updated: 2025-01-01
tags: [queue, messaging]
---

# Choose a message-queue approach

## Decision

Adopt **at-least-once delivery with idempotent consumers** for the order pipeline.

## Context

The order pipeline must not drop events, but the upstream broker can redeliver. We needed to
pick how consumers handle duplicates. See [[concepts/event-pipeline]] and
[[glossary/idempotency]] (example links — create those pages when relevant).

## Options considered

1. **At-least-once + idempotent consumers (chosen).** Broker may redeliver; consumers dedupe by
   a natural key. Simple broker config, robustness pushed into the consumer.
2. **Exactly-once via transactional outbox.** Strong guarantee, but more moving parts and
   operational burden than the current scale justifies. Rejected for now; revisit if dedup
   logic spreads across many consumers.
3. **At-most-once.** Simplest, but can drop events — unacceptable for orders. Rejected.

## Consequences

- Every consumer must implement dedup against a stable key — capture the pattern in
  [[concepts/event-pipeline]].
- Reconsider option 2 if idempotency logic becomes duplicated or error-prone.
```
