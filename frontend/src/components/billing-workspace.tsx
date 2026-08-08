"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { BillingSummaryResponse } from "@/lib/api/job-contract";
import { getApiErrorMessage } from "@/lib/api/resume-contract";

type BillingState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; summary: BillingSummaryResponse };

const capabilityLabels: Array<{
  key: keyof BillingSummaryResponse["entitlements"];
  label: string;
  detail: string;
}> = [
  {
    key: "job_discovery",
    label: "Job discovery",
    detail: "Search across connected providers from one workspace.",
  },
  {
    key: "explainable_recommendations",
    label: "Explainable recommendations",
    detail: "See why a role matches and what evidence is missing.",
  },
  {
    key: "application_tracking",
    label: "Application tracking",
    detail: "Keep statuses, decisions, and next actions together.",
  },
  {
    key: "reminders",
    label: "Application reminders",
    detail: "Stay ahead of the next actions you choose.",
  },
  {
    key: "tailored_documents",
    label: "Tailored documents",
    detail: "Factual resume and cover-letter assistance is planned for Pro.",
  },
];

function isBillingSummary(value: unknown): value is BillingSummaryResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "plan" in value &&
    "status" in value &&
    "entitlements" in value &&
    typeof value.entitlements === "object" &&
    value.entitlements !== null
  );
}

export function BillingWorkspace() {
  const [state, setState] = useState<BillingState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        setState({ status: "ready", summary: await requestSummary(controller.signal) });
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState(toBillingError(error));
      }
    })();
    return () => controller.abort();
  }, []);

  const retry = async () => {
    setState({ status: "loading" });
    try {
      setState({ status: "ready", summary: await requestSummary() });
    } catch (error) {
      setState(toBillingError(error));
    }
  };

  return (
    <main id="main-content" className="billing-main">
      <header className="billing-heading">
        <h1>Your plan, without the fine print.</h1>
        <p>
          See which Solara Hire capabilities are active today. Payment and
          upgrades stay unavailable until the full billing flow is ready.
        </p>
      </header>

      {state.status === "loading" && (
        <section className="billing-state-card" aria-busy="true" aria-live="polite">
          <span className="billing-skeleton billing-skeleton-short" />
          <span className="billing-skeleton billing-skeleton-title" />
          <span className="billing-skeleton" />
          <span className="billing-skeleton" />
          <span className="sr-only">Loading your plan details</span>
        </section>
      )}

      {state.status === "error" && (
        <section className="billing-state-card billing-error" role="alert">
          <span className="plan-seal">!</span>
          <div>
            <h2>Plan details are out of reach.</h2>
            <p>{state.message}</p>
            <button className="button" type="button" onClick={() => void retry()}>
              Try again
            </button>
          </div>
        </section>
      )}

      {state.status === "ready" && (
        <section className="billing-ledger" aria-labelledby="current-plan-title">
          <div className="billing-plan-summary">
            <div>
              <span className="plan-state">Current plan</span>
              <h2 id="current-plan-title">
                {state.summary.plan === "free" ? "Free" : "Pro"}
              </h2>
              <p>
                {state.summary.checkout_available
                  ? "Your plan can be managed securely from this account."
                  : "No payment method is required. Checkout is not available yet."}
              </p>
            </div>
            <span className="plan-seal" aria-label={`${state.summary.status} subscription`}>
              {state.summary.status === "active" ? "Active" : state.summary.status}
            </span>
          </div>

          <div className="billing-capabilities">
            <div className="billing-capabilities-heading">
              <h2>What your account can use</h2>
              <span>Effective access from the Solara Hire API</span>
            </div>
            <ul>
              {capabilityLabels.map((capability) => {
                const enabled = state.summary.entitlements[capability.key];
                return (
                  <li key={capability.key} className={enabled ? "is-enabled" : "is-planned"}>
                    <span className="capability-mark" aria-hidden="true">
                      {enabled ? "On" : "Soon"}
                    </span>
                    <div>
                      <strong>{capability.label}</strong>
                      <p>{capability.detail}</p>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>

          <aside className="billing-next-note">
            <div>
              <strong>Interested in what comes next?</strong>
              <p>Compare available capabilities with the planned Pro direction.</p>
            </div>
            <Link className="text-link" href="/pricing">
              View plans
            </Link>
          </aside>
        </section>
      )}
    </main>
  );
}

async function requestSummary(signal?: AbortSignal): Promise<BillingSummaryResponse> {
  const response = await fetch("/api/billing/summary", {
    cache: "no-store",
    signal,
  });
  const payload: unknown = await response.json();
  if (!response.ok || !isBillingSummary(payload)) {
    throw new Error(
      getApiErrorMessage(payload) ?? "Solara Hire could not load your plan details.",
    );
  }
  return payload;
}

function toBillingError(error: unknown): BillingState {
  return {
    status: "error",
    message:
      error instanceof Error
        ? error.message
        : "Solara Hire could not load your plan details.",
  };
}
