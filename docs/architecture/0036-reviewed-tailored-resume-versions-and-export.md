# 0036 — Complete tailored resumes with reviewed versions and exports

Status: accepted

## Decision

Solara Hire represents a tailored resume as an owner-scoped series of immutable versions. Each
version stores three complete snapshots: the source resume, the deterministic suggestion, and the
accepted result. The only automated transformation in this phase is ordering existing skills,
experience entries, and projects. A user can select the original or suggested ordering for each
section; saving changed choices creates a new version instead of mutating history.

Every new version starts in `pending_review`. PDF and DOCX exports remain unavailable until the
user explicitly confirms factual accuracy for the latest version. Confirmation changes the status
to `user_verified`, records the approval time, and unlocks both exports. Missing job skills remain
comparison evidence and never enter exported content.

Exports are generated on demand from the accepted snapshot. They are returned with private,
no-store response headers and are not written to application storage or analytics. The DOCX uses
the compact reference preset with a named `resume_compact` geometry override: US Letter, 0.65-inch
vertical margins, 0.72-inch horizontal margins, Arial typography, restrained green section rules,
real Word list paragraphs, and no running header or footer. The PDF renderer mirrors that system.

## API lifecycle

1. Create or load the latest draft from a factual tailoring plan.
2. Compare original, suggested, and accepted section ordering.
3. Save changed choices as a new version.
4. Confirm factual accuracy for the latest version.
5. Export the verified version as PDF or DOCX.

All reads, revisions, approvals, history, and downloads require the authenticated owner and the
`tailored_documents` entitlement. Stale versions cannot create revisions or receive approval.

## Consequences

- Tailored resume history is reproducible and survives process restarts.
- Exported documents contain only accepted source-resume facts.
- Access tokens remain in server-side Next.js handlers, including binary downloads.
- The user's original upload is never overwritten.
- Object-storage retention is unnecessary for this phase because exports are deterministic and
  generated on demand.
- ADR 0037 adds deterministic cover letters with editable, versioned content while retaining source
  evidence and a per-change acceptance boundary. LLM wording suggestions and object-storage
  delivery remain separate future milestones.
