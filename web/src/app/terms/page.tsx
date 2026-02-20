export default function TermsPage() {
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
          Terms of Service
        </h1>
        <p className="mt-2 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/30">
          Last updated: {new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}
        </p>

        <div className="mt-10 space-y-8 font-[family-name:var(--font-crimson-pro)] text-lg leading-relaxed text-[#e8f4ff]/70">
          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              1. What PRELUDE is
            </h2>
            <p>
              PRELUDE is a relationship compatibility analysis tool that uses AI to simulate
              potential relationship dynamics. Our simulations are probabilistic models — they
              are not predictions, guarantees, or clinical assessments. They are tools
              for self-reflection and informed decision-making.
            </p>
          </section>

          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              2. Not a replacement for professional advice
            </h2>
            <p>
              PRELUDE is not a mental health service, therapy platform, or relationship
              counselling service. Our compatibility reports are AI-generated simulations
              and should not be used as the sole basis for major relationship decisions.
              If you have mental health concerns, please consult a qualified professional.
            </p>
          </section>

          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              3. Eligibility
            </h2>
            <p>
              You must be at least 18 years old to use PRELUDE. By creating an account,
              you confirm that you meet this requirement.
            </p>
          </section>

          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              4. Acceptable use
            </h2>
            <p>
              You agree not to use PRELUDE to harass, stalk, or harm other users. You agree
              not to create fake profiles or misrepresent yourself during onboarding.
              You agree not to attempt to reverse-engineer other users&apos; psychological profiles.
            </p>
          </section>

          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              5. Simulation consent
            </h2>
            <p>
              When you initiate a simulation with another user, that user will be notified
              and will have access to the simulation results. By running a simulation, you
              consent to the other user receiving these results.
            </p>
          </section>

          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              6. Limitation of liability
            </h2>
            <p>
              PRELUDE&apos;s liability is limited to the amount you paid for the service in the
              preceding 12 months. We are not liable for relationship decisions made based
              on simulation results, emotional distress arising from simulation content,
              or inaccurate compatibility assessments.
            </p>
          </section>

          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              7. Changes to these terms
            </h2>
            <p>
              We may update these terms. We will notify you by email before material changes
              take effect. Continued use constitutes acceptance.
            </p>
          </section>

          <section>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff] mb-3">
              8. Contact
            </h2>
            <p>
              Questions about these terms: legal@prelude.app
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
