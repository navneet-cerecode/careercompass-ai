import type { Metadata } from "next";

import { CareerWorkspace } from "@/components/career-workspace";
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

        <CareerWorkspace />

        <footer className="site-footer">
          <span>Built for thoughtful career moves.</span>
          <span>Explainable matching · Human-reviewed decisions</span>
        </footer>
      </div>
    </>
  );
}
