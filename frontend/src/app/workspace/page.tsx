import type { Metadata } from "next";

import { CareerWorkspace } from "@/components/career-workspace";
import { SiteHeader } from "@/components/site-header";
import { getApiConnection } from "@/lib/api/client";
import { getSiteUser } from "@/lib/auth/session";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Your workspace · Solara Hire",
  description:
    "Turn your resume into a factual, reviewable profile before matching with jobs.",
};

export default async function WorkspacePage() {
  const [connection, user] = await Promise.all([
    getApiConnection(),
    getSiteUser(),
  ]);

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      <div className="site-shell workspace-shell">
        <SiteHeader
          connection={connection}
          user={user}
          activePage="workspace"
        />

        <CareerWorkspace
          user={
            user
              ? {
                  name: user.name,
                  email: user.email,
                  emailVerified: user.emailVerified,
                }
              : null
          }
        />

        <footer className="site-footer">
          <span>Built for thoughtful career moves.</span>
          <span>Explainable matching · Human-reviewed decisions</span>
        </footer>
      </div>
    </>
  );
}
