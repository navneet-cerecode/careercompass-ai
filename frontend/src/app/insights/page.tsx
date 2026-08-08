import type { Metadata } from "next";

import { SiteHeader } from "@/components/site-header";
import { SkillIntelligenceWorkspace } from "@/components/skill-intelligence-workspace";
import { getApiConnection } from "@/lib/api/client";
import { getSiteUser } from "@/lib/auth/session";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Skill intelligence · Solara Hire",
  description:
    "Compare reviewed resume evidence with requirements observed in the roles you chose.",
};

export default async function InsightsPage() {
  const [connection, user] = await Promise.all([getApiConnection(), getSiteUser()]);

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <div className="site-shell intelligence-shell">
        <SiteHeader connection={connection} user={user} activePage="insights" />
        {user?.emailVerified ? (
          <SkillIntelligenceWorkspace />
        ) : (
          <main id="main-content" className="saved-access-main">
            <section className="saved-access-card">
              <h1>
                {user
                  ? "Verify your email to compare private career evidence."
                  : "Sign in to see your skill intelligence."}
              </h1>
              <p>
                Resume skills and chosen-role history are private account data and require a
                verified identity.
              </p>
              <a className="button" href={user ? "/auth/logout" : "/auth/login"}>
                {user ? "Sign out after verification" : "Sign in securely"}
              </a>
            </section>
          </main>
        )}
        <footer className="site-footer">
          <span>Built from the roles you chose.</span>
          <span>Observed evidence · Explicit limits · No invented demand</span>
        </footer>
      </div>
    </>
  );
}
