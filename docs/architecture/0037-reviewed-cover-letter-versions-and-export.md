# 0037 — Generate cover letters from verified evidence

Status: accepted

## Decision

Solara Hire creates cover-letter suggestions deterministically from an owner-scoped factual
tailoring plan, its source resume, and the canonical target job. The suggestion may identify the
job and company, list matched skills already present in the resume, and quote selected experience
or project evidence. It must not add missing skills, metrics, responsibilities, employers, dates,
or personal motivation that the user did not provide.

The user may edit the greeting, opening, evidence paragraph, motivation paragraph, closing, and
sign-off. Candidate identity and target-job fields remain locked to their persisted sources. Every
saved edit creates an immutable version, returns to `pending_review`, and retains the original
evidence ledger. Export is unavailable until the owner explicitly confirms every candidate claim
in the latest version.

PDF and DOCX exports are generated on demand from the accepted version with private, no-store
responses. They are not persisted to object storage or analytics. Document metadata does not name
the author or editor.

## API lifecycle

1. Create or load the latest draft for a factual tailoring plan.
2. Inspect its verified evidence and edit the accepted content.
3. Save edits as a new version.
4. Confirm factual accuracy for the latest version.
5. Export the verified version as PDF or DOCX.

All operations require the authenticated owner and the existing `tailored_documents` entitlement.
Stale versions cannot create revisions or receive approval.

## Consequences

- Cover letters are useful without placing unsupported prose behind an AI-confidence claim.
- Users retain final authorship and responsibility for any text they add.
- Missing job skills never enter the suggestion.
- Later LLM styling can propose wording only after it preserves this evidence ledger, immutable
  version history, and explicit approval boundary.
