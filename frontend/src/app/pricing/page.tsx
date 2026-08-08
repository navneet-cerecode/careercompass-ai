import type { Metadata } from "next";
import Link from "next/link";

import { SiteHeader } from "@/components/site-header";
import { getApiConnection } from "@/lib/api/client";
import { getSiteUser } from "@/lib/auth/session";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Plans · Solara Hire",
  description: "See what Solara Hire includes during the beta and what is planned for Pro.",
};

const freeCapabilities = [
  "Search connected job providers",
  "Rank roles against your resume",
  "Review explainable match evidence",
  "Save roles and track applications",
  "Set next actions and reminders",
  "Create reviewed tailored resumes and cover letters",
];

const plannedCapabilities = [
  "Higher search and document limits",
  "Evidence-bound AI wording suggestions",
  "A secure payment and plan-management flow",
];

export default async function PricingPage() {
  const [connection, user] = await Promise.all([getApiConnection(), getSiteUser()]);

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <div className="site-shell pricing-shell">
        <SiteHeader connection={connection} user={user} activePage="pricing" />
        <main id="main-content" className="pricing-main">
          <header className="pricing-hero">
            <h1>Start with the work that matters.</h1>
            <p>
              Solara Hire is free while we build the complete Pro experience.
              No hidden checkout, invented limits, or silent upgrades.
            </p>
          </header>

          <section className="plan-comparison" aria-label="Solara Hire plans">
            <article className="plan-card plan-card-current">
              <div className="plan-card-intro">
                <span className="plan-state">Available now</span>
                <h2>Free</h2>
                <p>Use the working career workspace without entering payment details.</p>
                <Link className="button" href={user ? "/settings/billing" : "/auth/login?screen_hint=signup"}>
                  {user ? "View your access" : "Create account"}
                </Link>
              </div>
              <div className="plan-capability-list">
                <strong>Included today</strong>
                <ul>
                  {freeCapabilities.map((capability) => (
                    <li key={capability}><span className="plan-list-mark" aria-hidden="true" />{capability}</li>
                  ))}
                </ul>
              </div>
            </article>

            <article className="plan-card plan-card-planned">
              <div className="plan-card-intro">
                <span className="plan-state">Planned</span>
                <h2>Pro</h2>
                <p>
                  A future paid plan for expanded limits and advanced career workflows.
                  Pricing has not been set.
                </p>
                <button className="button button-muted" type="button" disabled>
                  Not available yet
                </button>
              </div>
              <div className="plan-capability-list">
                <strong>Direction, not a promise</strong>
                <ul>
                  {plannedCapabilities.map((capability) => (
                    <li key={capability}><span className="plan-list-mark is-hollow" aria-hidden="true" />{capability}</li>
                  ))}
                </ul>
              </div>
            </article>
          </section>

          <aside className="pricing-principle">
            <strong>Your judgment remains the final step.</strong>
            <p>Solara Hire assists with discovery and decisions. It does not auto-apply or invent resume claims.</p>
          </aside>
        </main>
        <footer className="site-footer">
          <span>Built for thoughtful career moves.</span>
          <span>Clear plans · Human review · No auto-apply</span>
        </footer>
      </div>
    </>
  );
}
