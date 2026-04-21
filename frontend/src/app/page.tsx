import Link from "next/link";

import { Card } from "@/shared/components/ui/Card";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto flex max-w-5xl flex-col gap-12 px-6 pb-24 pt-16 md:pt-24">
        <header className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div className="space-y-4">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-emerald-400/90">
              Governance · Not a chatbot
            </p>
            <h1 className="text-4xl font-semibold tracking-tight text-white md:text-5xl">
              Autonomous Cybersecurity Compliance &amp; Incident Escalation AI
            </h1>
            <p className="max-w-2xl text-base leading-relaxed text-zinc-400">
              The system ingests incidents, retrieves regulatory grounding, scores risk, determines
              obligations, proposes escalation, and audits its own reasoning — with MCP-isolated data
              access and stored traceability.
            </p>
          </div>
          <div className="flex shrink-0 flex-col gap-3 md:items-end">
            <Link
              href="/sign-in"
              className="inline-flex w-full min-w-[160px] items-center justify-center rounded-lg bg-emerald-500/90 px-5 py-2.5 text-sm font-semibold text-zinc-950 hover:bg-emerald-400 md:w-auto"
            >
              Sign in
            </Link>
            <Link href="/sign-up" className="text-sm text-zinc-500 hover:text-zinc-300">
              Create access
            </Link>
          </div>
        </header>

        <div className="grid gap-4 md:grid-cols-3">
          {[
            {
              title: "Log intelligence",
              body: "Structures facts: PII exposure, scope, timeline, severity hint.",
            },
            {
              title: "RAG compliance",
              body: "Hybrid search across NIST CSF, ISO 27001, ENISA, GDPR-style seeds.",
            },
            {
              title: "Critic / auditor",
              body: "Reflection loop: citations, deadlines, hallucination risk, escalation fit.",
            },
          ].map((x) => (
            <Card key={x.title} className="p-5">
              <h2 className="text-sm font-semibold text-emerald-300">{x.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-zinc-400">{x.body}</p>
            </Card>
          ))}
        </div>

        <Card className="border-emerald-900/40 bg-gradient-to-br from-zinc-950 to-emerald-950/30 p-8">
          <h2 className="text-lg font-semibold text-white">Operational questions this engine answers</h2>
          <ul className="mt-4 grid gap-3 text-sm text-zinc-300 md:grid-cols-2">
            {[
              "Was personal data involved?",
              "Is regulatory reporting mandatory?",
              "What is the deadline window?",
              "Which internal controls failed or are in doubt?",
              "What penalties could plausibly apply (illustrative, counsel-reviewed in production)?",
            ].map((q) => (
              <li
                key={q}
                className="rounded-lg border border-zinc-800/80 bg-black/30 px-4 py-3"
              >
                {q}
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
