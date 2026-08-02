import Link from "next/link";

import { ConnectionStatus } from "@/components/connection-status";
import type { ApiConnection } from "@/lib/api/client";
import type { SiteUser } from "@/lib/auth/session";

type SiteHeaderProps = {
  connection: ApiConnection;
  user: SiteUser | null;
  activePage?: "home" | "workspace" | "saved" | "applications";
};

export function SiteHeader({
  connection,
  user,
  activePage = "home",
}: SiteHeaderProps) {
  return (
    <header className="site-header">
      <Link className="brand" href="/" aria-label="Solara Hire home">
        <span className="brand-mark" aria-hidden="true">
          <span />
        </span>
        <span>Solara Hire</span>
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
        {user && (
          <>
            <Link
              href="/saved"
              aria-current={activePage === "saved" ? "page" : undefined}
            >
              Saved
            </Link>
            <Link
              href="/applications"
              aria-current={
                activePage === "applications" ? "page" : undefined
              }
            >
              Tracker
            </Link>
          </>
        )}
        <Link href="/#trust">Trust</Link>
      </nav>

      <div className="header-tools">
        <ConnectionStatus connection={connection} />
        {user ? (
          <div className="account-menu">
            <span className="account-avatar" aria-hidden="true">
              {user.name.slice(0, 1).toUpperCase()}
            </span>
            <span className="account-copy">
              <strong>{user.name}</strong>
              <span>
                {user.emailVerified
                  ? user.email ?? "Verified account"
                  : "Verify your email"}
              </span>
            </span>
            <a className="account-action" href="/auth/logout">
              Sign out
            </a>
          </div>
        ) : (
          <div className="auth-actions">
            <a className="auth-link" href="/auth/login">
              Sign in
            </a>
            <a
              className="auth-signup"
              href="/auth/login?screen_hint=signup"
            >
              Create account
            </a>
          </div>
        )}
      </div>
    </header>
  );
}
