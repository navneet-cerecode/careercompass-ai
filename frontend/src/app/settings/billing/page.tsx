import type { Metadata } from "next";

import { BillingWorkspace } from "@/components/billing-workspace";
import { SiteHeader } from "@/components/site-header";
import { getApiConnection } from "@/lib/api/client";
import { getSiteUser } from "@/lib/auth/session";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Plan and access · Solara Hire",
  description: "Review your current Solara Hire plan and effective product access.",
};

export default async function BillingPage() {
  const [connection, user] = await Promise.all([getApiConnection(), getSiteUser()]);

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <div className="site-shell billing-shell">
        <SiteHeader connection={connection} user={user} />
        {user?.emailVerified ? (
          <BillingWorkspace />
        ) : (
          <main id="main-content" className="saved-access-main">
            <section className="saved-access-card">
              <span className="micro-label">Private account details</span>
              <h1>{user ? "Verify your email to view your plan." : "Sign in to view your plan."}</h1>
              <p>Plan details and account access require a verified identity.</p>
              <a className="button" href={user ? "/auth/logout" : "/auth/login"}>
                {user ? "Sign out after verification" : "Sign in securely"}
              </a>
            </section>
          </main>
        )}
        <footer className="site-footer">
          <span>Clear access. No surprise charges.</span>
          <span>Review-first by design</span>
        </footer>
      </div>
    </>
  );
}
