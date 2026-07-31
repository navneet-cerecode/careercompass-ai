import Link from "next/link";

import { ConnectionStatus } from "@/components/connection-status";
import type { ApiConnection } from "@/lib/api/client";

type SiteHeaderProps = {
  connection: ApiConnection;
  activePage?: "home" | "workspace";
};

export function SiteHeader({
  connection,
  activePage = "home",
}: SiteHeaderProps) {
  return (
    <header className="site-header">
      <Link className="brand" href="/" aria-label="CareerCompass AI home">
        <span className="brand-mark" aria-hidden="true">
          <span />
        </span>
        <span>CareerCompass</span>
        <span className="brand-ai">AI</span>
      </Link>

      <nav className="main-nav" aria-label="Primary navigation">
        <Link href="/#approach">How it works</Link>
        <Link
          href="/workspace"
          aria-current={activePage === "workspace" ? "page" : undefined}
        >
          Workspace
        </Link>
        <Link href="/#trust">Trust</Link>
      </nav>

      <ConnectionStatus connection={connection} />
    </header>
  );
}
