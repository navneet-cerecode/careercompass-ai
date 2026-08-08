# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Solara Hire serves job seekers across technical and non-technical careers. Users bring a real
resume, review extracted facts, discover suitable roles, and decide which opportunities and
application actions to pursue.

## Product Purpose

Solara Hire helps people move from a factual career profile to explainable job recommendations,
reviewed application materials, and deliberate follow-through. Success means users understand why
a role fits, what evidence supports that conclusion, and what they must review or do next.

## Positioning

Solara Hire connects each recommendation and generated document to user-reviewed resume evidence,
keeps employer-side decisions under the user's control, and discloses gaps instead of silently
rewriting a candidate's history.

## Operating Context

The core workflow is resume upload and review, preferences, provider-based job discovery,
normalization and deduplication, explainable ranking, saved jobs, application tracking, reviewed
documents, application packets, and interview preparation. The product uses external job sources
and links users to verified employer or provider pages for final review and submission.

## Capabilities and Constraints

- The canonical web application is Next.js backed by FastAPI and PostgreSQL.
- Job discovery is provider-based and must retain source attribution and partial-result disclosure.
- Resume tailoring, cover letters, and interview notes must preserve factual accuracy.
- Application actions are assisted and review-first; unattended mass applying is out of scope.
- Authentication, persistence, subscriptions, and background-worker boundaries already exist.
- New career intelligence must support cross-industry skills and distinguish observed product data
  from broader labor-market claims.

## Brand Commitments

The product name is Solara Hire. Its voice is clear, calm, direct, and evidence-led. The interface
must feel intentional and high quality while keeping controls familiar and decisions legible.

## Evidence on Hand

The repository contains user-reviewed resume facts, normalized job records, provider attribution,
recommendation components, saved jobs, application history, and reviewed application documents.
It contains no representative labor-market dataset, customer testimonials, hiring-outcome
benchmarks, or employer-side application status feed; future work must not fabricate them.

## Product Principles

- Evidence before assertion.
- Explain every consequential score or recommendation.
- Keep the user in control of employer-facing actions.
- Serve technical and non-technical careers equally.
- Improve incrementally with tested, reversible changes.

## Accessibility & Inclusion

Core workflows must be keyboard accessible, readable across desktop and mobile layouts, and usable
without relying on color alone. Language and skill examples must not assume a technical career.
