import type { Metadata } from "next";

import { ApplicationTrackerWorkspace } from "@/components/application-tracker-workspace";
import { SiteHeader } from "@/components/site-header";
import { getApiConnection } from "@/lib/api/client";
import { getSiteUser } from "@/lib/auth/session";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Application tracker · Solara Hire",
  description:
    "Keep application next steps, status changes, and decision history in one review-first workspace.",
};

export default async function ApplicationsPage() {
  const [connection, user] = await Promise.all([
    getApiConnection(),
    getSiteUser(),
  ]);

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <div className="site-shell application-tracker-shell">
        <SiteHeader
          connection={connection}
          user={user}
          activePage="applications"
        />
        {user?.emailVerified ? (
          <ApplicationTrackerWorkspace />
        ) : (
          <main id="main-content" className="saved-access-main">
            <section className="saved-access-card">
              <span className="micro-label">Private application history</span>
              <h1>
                {user
                  ? "Verify your email to use the tracker."
                  : "Sign in to track your applications."}
              </h1>
              <p>
                Status changes and application notes are private account data
                and require a verified identity.
              </p>
              {user ? (
                <a className="button" href="/auth/logout">
                  Sign out after verification
                </a>
              ) : (
                <a className="button" href="/auth/login">
                  Sign in securely
                </a>
              )}
            </section>
          </main>
        )}
        <footer className="site-footer">
          <span>Built for deliberate applications.</span>
          <span>Your history · Your decisions · No auto-apply</span>
        </footer>
      </div>
    </>
  );
}
