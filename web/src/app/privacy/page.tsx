export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-[#020408] px-4 py-24">
      <div className="mx-auto max-w-2xl">
        <a
          href="/match"
          className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/30 hover:text-[#e8f4ff]/60 transition-colors"
        >
          ← PRELUDE
        </a>

        <h1 className="mt-8 font-[family-name:var(--font-syne)] text-3xl font-extrabold text-[#e8f4ff]">
          Privacy Policy
        </h1>
        <p className="mt-2 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/30">
          Last updated: {new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}
        </p>

        <div className="mt-10 space-y-8 font-[family-name:var(--font-crimson-pro)] text-lg leading-relaxed text-[#e8f4ff]/70">
          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              What we collect
            </h2>
            <p>
              PRELUDE collects the information you provide during onboarding: your attachment style,
              value rankings, fear architecture, communication patterns, and relationship history.
              This is your Shadow Vector — the psychological profile that powers your simulations.
            </p>
            <p className="mt-3">
              We also collect your email address, city, and account information via Clerk
              (our authentication provider). We do not collect your real name unless you choose
              to provide it.
            </p>
          </section>

          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              How we use it
            </h2>
            <p>
              Your Shadow Vector is used exclusively to run compatibility simulations. It is stored
              as a numerical vector and is never shared with other users directly. Simulation results
              (transcripts, belief states, compatibility scores) are stored and associated with your account.
            </p>
            <p className="mt-3">
              We do not sell your data. We do not use your psychological profile for advertising.
            </p>
          </section>

          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              Sharing and disclosure
            </h2>
            <p>
              When you run a simulation with another user, they may see the simulation
              results and a summary of your compatibility analysis. They will not see your raw
              Shadow Vector or onboarding answers.
            </p>
            <p className="mt-3">
              We share data with: Clerk (authentication), Resend (transactional email),
              Anthropic (AI inference — simulation dialogues are sent to Anthropic&apos;s API).
              We do not share data with any other third parties.
            </p>
          </section>

          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              Your rights
            </h2>
            <p>
              You can request deletion of all your data at any time by contacting us at
              privacy@tryprior.xyz or via the Settings page. We will delete your profile,
              Shadow Vector, and all simulation data within 30 days.
            </p>
          </section>

          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              Data security
            </h2>
            <p>
              Your data is stored in encrypted PostgreSQL databases. All API communication
              is encrypted via HTTPS. We use industry-standard practices for data protection.
            </p>
          </section>

          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              Contact
            </h2>
            <p>
              Questions about privacy: privacy@tryprior.xyz
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
