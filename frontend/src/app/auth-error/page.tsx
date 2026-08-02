import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Sign-in interrupted · Solara Hire",
  description: "Return safely to Solara Hire after an interrupted sign-in.",
};

export default function AuthErrorPage() {
  return (
    <main className="auth-error-page">
      <section className="auth-error-card" aria-labelledby="auth-error-title">
        <Link className="brand auth-error-brand" href="/">
          <span className="brand-mark" aria-hidden="true">
            <span />
          </span>
          <span>Solara Hire</span>
          <span className="brand-ai">AI</span>
        </Link>

        <span className="auth-error-symbol" aria-hidden="true">
          !
        </span>
        <span className="micro-label">Secure sign-in interrupted</span>
        <h1 id="auth-error-title">Nothing was saved or changed.</h1>
        <p>
          The identity provider could not complete this sign-in. Retry the
          secure flow, or return to the anonymous workspace.
        </p>
        <div className="auth-error-actions">
          <a className="button button-primary" href="/auth/login">
            Try signing in again
          </a>
          <Link className="button button-secondary" href="/workspace">
            Continue without an account
          </Link>
        </div>
      </section>
    </main>
  );
}
