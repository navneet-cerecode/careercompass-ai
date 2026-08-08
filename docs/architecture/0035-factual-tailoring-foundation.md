# 0035 — Start resume tailoring with factual ordering

Status: accepted

## Decision

The first tailoring boundary is deterministic and non-generative. It may reorder existing skills,
experience entries, and projects according to target-job relevance; it may not rewrite text or add
skills, metrics, responsibilities, employers, projects, or dates. Missing job skills remain explicit
gaps and are never inserted into candidate content.

Every prioritized experience or project item retains its original source index and exact source
text. A tailoring plan always requires user review and carries an algorithm version. Later LLM
rewriting must produce suggestions against this evidence contract and cannot silently mutate the
source resume.

Canonical jobs persist their normalized required skills so matched and missing skill evidence
survives process boundaries and can be reproduced when a plan is loaded later.

## Consequences

Solara Hire can build a comparison and approval experience on a safe, testable foundation before
adding generated prose or background execution. ADR 0036 adds persistence, versioned decisions,
explicit factual approval, and reviewed exports without weakening this evidence boundary.
