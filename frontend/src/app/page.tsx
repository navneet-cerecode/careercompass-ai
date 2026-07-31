import { ConnectionStatus } from "@/components/connection-status";
import { getApiConnection } from "@/lib/api/client";

export const dynamic = "force-dynamic";

const signals = [
  {
    number: "01",
    title: "Bring your real story",
    description:
      "Your resume becomes a profile you can review—not a black box the AI silently rewrites.",
  },
  {
    number: "02",
    title: "See the market clearly",
    description:
      "Jobs from multiple sources are normalized, de-duplicated, and ranked against the same evidence.",
  },
  {
    number: "03",
    title: "Act with context",
    description:
      "Every recommendation shows its signals, missing skills, and the next sensible move.",
  },
];

export default async function Home() {
  const connection = await getApiConnection();

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      <div className="site-shell">
        <header className="site-header">
          <a className="brand" href="#" aria-label="CareerCompass AI home">
            <span className="brand-mark" aria-hidden="true">
              <span />
            </span>
            <span>CareerCompass</span>
            <span className="brand-ai">AI</span>
          </a>

          <nav className="main-nav" aria-label="Primary navigation">
            <a href="#approach">How it works</a>
            <a href="#workspace">Workspace</a>
            <a href="#trust">Trust</a>
          </nav>

          <ConnectionStatus connection={connection} />
        </header>

        <main id="main-content">
          <section className="hero" aria-labelledby="hero-title">
            <div className="hero-copy">
              <div className="eyebrow">
                <span aria-hidden="true">✦</span>
                Career intelligence, grounded in your story
              </div>
              <h1 id="hero-title">
                Move with clarity.
                <span>Not guesswork.</span>
              </h1>
              <p className="hero-intro">
                CareerCompass turns your experience into an explainable view of
                where you fit, what you are missing, and which opportunity
                deserves your energy next.
              </p>

              <div className="hero-actions">
                <a className="button button-primary" href="#workspace">
                  Open your workspace
                  <span aria-hidden="true">↗</span>
                </a>
                <a className="button button-secondary" href="#approach">
                  See the matching model
                </a>
              </div>

              <div className="hero-proof" id="trust">
                <div>
                  <strong>Factual-first</strong>
                  <span>No invented experience</span>
                </div>
                <div>
                  <strong>Explainable</strong>
                  <span>Signals you can inspect</span>
                </div>
                <div>
                  <strong>User-reviewed</strong>
                  <span>You approve every action</span>
                </div>
              </div>
            </div>

            <div className="signal-stage" id="workspace">
              <div className="stage-glow" aria-hidden="true" />
              <div className="stage-label">
                <span>Workspace preview</span>
                <span className="stage-index">CC / 01</span>
              </div>

              <div className="match-card">
                <div className="match-card-top">
                  <div>
                    <span className="micro-label">Your strongest lane</span>
                    <h2>Product-minded AI Engineer</h2>
                  </div>
                  <div className="match-orbit" aria-label="Strong match preview">
                    <span>86</span>
                    <small>fit</small>
                  </div>
                </div>

                <div className="role-meta">
                  <span>Remote-friendly</span>
                  <span>Early career</span>
                  <span>Full time</span>
                </div>

                <div className="signal-grid">
                  <div className="signal-row">
                    <div>
                      <span>Skill evidence</span>
                      <strong>Strong</strong>
                    </div>
                    <div className="signal-track">
                      <span style={{ width: "88%" }} />
                    </div>
                  </div>
                  <div className="signal-row">
                    <div>
                      <span>Role alignment</span>
                      <strong>Clear</strong>
                    </div>
                    <div className="signal-track">
                      <span style={{ width: "78%" }} />
                    </div>
                  </div>
                  <div className="signal-row">
                    <div>
                      <span>Growth edge</span>
                      <strong>2 skills</strong>
                    </div>
                    <div className="signal-track signal-track-warm">
                      <span style={{ width: "42%" }} />
                    </div>
                  </div>
                </div>

                <div className="next-move">
                  <span className="next-move-icon" aria-hidden="true">
                    ↳
                  </span>
                  <div>
                    <span className="micro-label">Recommended next move</span>
                    <strong>Review the two missing skills before applying</strong>
                  </div>
                </div>
              </div>

              <div className="floating-note floating-note-top">
                <span className="note-dot" />
                <div>
                  <strong>Source-aware</strong>
                  <span>Duplicates merged</span>
                </div>
              </div>
              <div className="floating-note floating-note-bottom">
                <span className="note-arrow">↑</span>
                <div>
                  <strong>Evidence over hype</strong>
                  <span>Every score has a reason</span>
                </div>
              </div>
            </div>
          </section>

          <section className="approach" id="approach" aria-labelledby="approach-title">
            <div className="section-heading">
              <span className="micro-label">The CareerCompass method</span>
              <h2 id="approach-title">
                One profile.
                <br />
                Three better decisions.
              </h2>
            </div>

            <div className="approach-grid">
              {signals.map((signal) => (
                <article key={signal.number} className="approach-card">
                  <span className="approach-number">{signal.number}</span>
                  <div>
                    <h3>{signal.title}</h3>
                    <p>{signal.description}</p>
                  </div>
                </article>
              ))}
            </div>
          </section>
        </main>

        <footer className="site-footer">
          <span>Built for thoughtful career moves.</span>
          <span>Phase 4 · Frontend foundation</span>
        </footer>
      </div>
    </>
  );
}
