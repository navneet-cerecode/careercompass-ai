import type { Metadata } from "next";

import { ResumeOnboarding } from "@/components/resume-onboarding";
import { SiteHeader } from "@/components/site-header";
import { getApiConnection } from "@/lib/api/client";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Your workspace · CareerCompass AI",
  description:
    "Turn your resume into a factual, reviewable profile before matching with jobs.",
};

export default async function WorkspacePage() {
  const connection = await getApiConnection();

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      <div className="site-shell workspace-shell">
        <SiteHeader connection={connection} activePage="workspace" />

        <main id="main-content" className="workspace-main">
          <section
            className="workspace-intro"
            aria-labelledby="workspace-title"
          >
            <div className="workspace-progress" aria-label="Onboarding progress">
              <span className="is-current">01</span>
              <span>Profile</span>
              <span className="progress-line" aria-hidden="true" />
              <span>02</span>
              <span>Preferences</span>
              <span className="progress-line" aria-hidden="true" />
              <span>03</span>
              <span>Matches</span>
            </div>

            <span className="micro-label">Your private workspace</span>
            <h1 id="workspace-title">
              Let&apos;s map what
              <span>you already know.</span>
            </h1>
            <p>
              Upload your current resume. CareerCompass will extract a profile
              for you to inspect before it scores a single opportunity.
            </p>

            <div className="workspace-promises">
              <div>
                <span aria-hidden="true">01</span>
                <strong>No silent rewriting</strong>
              </div>
              <div>
                <span aria-hidden="true">02</span>
                <strong>You review the evidence</strong>
              </div>
              <div>
                <span aria-hidden="true">03</span>
                <strong>No automatic applications</strong>
              </div>
            </div>
          </section>

          <div className="workspace-panel">
            <ResumeOnboarding />
          </div>
        </main>

        <footer className="site-footer">
          <span>Built for thoughtful career moves.</span>
          <span>Phase 4B · Resume onboarding</span>
        </footer>
      </div>
    </>
  );
}
