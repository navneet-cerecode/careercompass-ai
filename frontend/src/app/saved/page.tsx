import type { Metadata } from "next";

import { SavedJobsWorkspace } from "@/components/saved-jobs-workspace";
import { SiteHeader } from "@/components/site-header";
import { getApiConnection } from "@/lib/api/client";
import { getSiteUser } from "@/lib/auth/session";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Saved roles · Solara Hire",
  description:
    "Review the opportunities you saved before choosing your next application.",
};

export default async function SavedJobsPage() {
  const [connection, user] = await Promise.all([
    getApiConnection(),
    getSiteUser(),
  ]);

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <div className="site-shell saved-jobs-shell">
        <SiteHeader connection={connection} user={user} activePage="saved" />
        {user?.emailVerified ? (
          <SavedJobsWorkspace />
        ) : (
          <main id="main-content" className="saved-access-main">
            <section className="saved-access-card">
              <span className="micro-label">Private shortlist</span>
              <h1>
                {user ? "Verify your email to save roles." : "Sign in to keep a shortlist."}
              </h1>
              <p>
                Saved jobs are private account data and require a verified
                identity.
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
          <span>Built for thoughtful career moves.</span>
          <span>Saved by you · Never auto-applied</span>
        </footer>
      </div>
    </>
  );
}
