# Frontend cutover contract

## Current product surface

The Next.js application in `frontend/` is the canonical Solara Hire web interface. Its
`/workspace` route owns both the standard anonymous journey and the same owner-scoped journey
when an Auth0 session is present:

1. upload and parse a resume;
2. review and correct structured facts for the current session;
3. set explicit role and location preferences;
4. discover normalized, deduplicated jobs through FastAPI;
5. rank those jobs against the reviewed profile;
6. inspect score components, matched skills, missing skills, and preparation guidance;
7. save promising roles to a private, owner-scoped shortlist;
8. explicitly start and update an owner-scoped application tracker;
9. compare original, suggested, and accepted tailored-resume sections;
10. save versioned review decisions and confirm factual accuracy;
11. export an approved tailored resume as PDF or DOCX;
12. draft a cover letter from verified resume and job evidence;
13. edit, version, fact-check, and export the approved cover letter;
14. open the verified job page for user review.

FastAPI remains the source of truth for transport contracts and Python application services
remain the source of truth for parsing, discovery, normalization, persistence, and ranking.
Next.js route handlers are narrow server-side proxies, not a second backend.

## Compatibility fallback

The root `app.py` Streamlit interface remains runnable as a compatibility fallback:

```powershell
.\venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit is frozen for compatibility and critical fixes. New product work belongs in Next.js
and FastAPI. Do not delete the fallback until the production rollout has an accepted rollback
window and every required fallback-only capability has a replacement.

## Feature-parity gate

| Capability | Next.js | Streamlit fallback | Cutover decision |
| --- | --- | --- | --- |
| PDF, DOCX, and TXT upload | Complete | Complete | Next.js canonical |
| Temporary parsing with source review | Complete | Complete | Next.js canonical |
| User correction of parsed facts | Complete | Not available | Next.js canonical |
| Role and location preferences | Complete | Complete | Next.js canonical |
| Provider discovery, normalization, and deduplication | Complete through FastAPI | Complete through Python services | Shared backend |
| Explainable deterministic ranking | Complete | Complete | Next.js canonical |
| Provider coverage and partial-result disclosure | Complete | Limited | Next.js canonical |
| External application review | Complete | Complete | Assisted workflow only |
| On-demand Groq recruiter narrative | Not exposed in the web workflow | Available in AI Inspector | Compatibility exception |
| Verified browser identity and owner-scoped resume/search persistence | Complete | Not available | Next.js canonical |
| Saved jobs | Complete for verified accounts | Not production-ready | Next.js canonical |
| Application tracking | Complete for verified accounts | Not production-ready | Next.js canonical |
| Reviewed, versioned tailored resumes | Complete for entitled verified accounts | Not available | Next.js canonical |
| Reviewed, versioned cover letters | Complete for entitled verified accounts | Not available | Next.js canonical |

The Streamlit-only Groq narrative is not part of the anonymous cutover gate. Moving long-running
AI generation into the web product should use the Phase 5 worker boundary rather than blocking a
request or duplicating the legacy UI call.

## Cutover smoke gate

With PostgreSQL, FastAPI, and Next.js running locally:

```powershell
.\venv\Scripts\python.exe scripts\smoke_frontend.py
```

The smoke command is deliberately non-destructive. It verifies API liveness/readiness and the
server-rendered home and workspace routes. It does not upload a resume, call paid providers,
invoke Groq, mutate application data, or print credentials.

Before merging a cutover change, also run:

```powershell
.\venv\Scripts\python.exe -m pytest
Set-Location frontend
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build
```

## Removal gate for Streamlit

Removing Streamlit requires a separate approved change after all of the following are true:

- the Next.js workflow is deployed and monitored in production;
- authenticated ownership and persistence are available where required;
- long-running AI work has a worker-backed web flow if the narrative remains a product feature;
- production rollback procedures have been exercised;
- no supported documentation or automation still points to Streamlit as the normal interface.
