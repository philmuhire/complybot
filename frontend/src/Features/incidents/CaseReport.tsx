"use client";

import { useMemo } from "react";

import { Badge } from "@/shared/components/ui/Badge";
import { Card } from "@/shared/components/ui/Card";

import type { PipelineBundle } from "./incidents.types";

/** `/api/incidents/analyze` returns `{ pipeline }` at top level (not wrapped in final_report). */
export function pipelineBundleFromAnalyze(data: unknown): PipelineBundle | null {
  if (!data || typeof data !== "object") return null;
  const p = (data as { pipeline?: unknown }).pipeline;
  if (!p || typeof p !== "object") return null;
  return p as PipelineBundle;
}

function num(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number" && Number.isFinite(v)) return String(v);
  return String(v);
}

function boolYesNo(v: unknown): string {
  return v === true ? "Yes" : v === false ? "No" : "—";
}

function str(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "string") return v || "—";
  return String(v);
}

export function extractPipelineBundle(finalReport: unknown): PipelineBundle | null {
  if (!finalReport || typeof finalReport !== "object") return null;
  const p = (finalReport as { pipeline?: unknown }).pipeline;
  if (!p || typeof p !== "object") return null;
  return p as PipelineBundle;
}

function buildNextSteps(
  bundle: PipelineBundle | null,
  incidentStatus: string | undefined,
): string[] {
  const steps: string[] = [];
  const obl = bundle?.obligations as Record<string, unknown> | undefined;
  const esc = bundle?.escalation as Record<string, unknown> | undefined;
  const critic = bundle?.critic as Record<string, unknown> | undefined;

  if (obl?.authority_notification_required === true) {
    const h = obl.authority_deadline_hours;
    steps.push(
      typeof h === "number"
        ? `Treat regulator / authority notification as potentially due within approximately ${h} hours where your counsel confirms a duty exists.`
        : `Assess regulator or supervisory notification requirements with counsel; prepare drafts if a duty applies.`,
    );
  } else if (obl) {
    steps.push(
      `No mandatory authority notification was inferred by the obligation model — still validate with counsel if facts change.`,
    );
  }

  if (obl?.user_notification_required === true) {
    steps.push(`Plan affected-user or customer communications per your playbooks and any retrieved citation duties.`);
  }

  if (obl?.board_escalation_required === true) {
    steps.push(`Escalate to board or executive governance per internal policy.`);
  }

  const checklist = esc?.documentation_checklist;
  if (Array.isArray(checklist)) {
    for (const item of checklist) {
      if (typeof item === "string" && item.trim()) steps.push(item.trim());
    }
  }

  const cd = esc?.countdown_hours;
  if (typeof cd === "number" && Number.isFinite(cd)) {
    steps.push(
      `Internal escalation / response clock referenced at ~${cd} hours — align IR and legal leads on milestones.`,
    );
  }

  const level = esc?.level;
  if (typeof level === "string" && level && level !== "internal") {
    steps.push(`Escalation tier suggested: ${level.replace(/_/g, " ")} — route to the owning role on-call.`);
  }

  if (critic?.passed === false || incidentStatus === "needs_review") {
    steps.push(`Schedule human review: critic gate did not pass or case is marked needs_review — validate citations and obligations with GRC/legal.`);
  }

  const missing = critic?.missing_dimensions;
  if (Array.isArray(missing) && missing.length > 0) {
    steps.push(`Close gaps noted by audit: ${missing.filter((x) => typeof x === "string").join("; ")}.`);
  }

  if (steps.length === 0) {
    steps.push(`Confirm retention of evidence, ticket linkage, and post-incident lessons learned with your IR lead.`);
  }

  const seen = new Set<string>();
  return steps.filter((s) => {
    if (seen.has(s)) return false;
    seen.add(s);
    return true;
  });
}

type Props = {
  bundle: PipelineBundle | null;
  incidentId: string;
  status: string;
  deadlineAt: string | null;
};

export function CaseReport({ bundle, incidentId, status, deadlineAt }: Props) {
  const nextSteps = useMemo(() => buildNextSteps(bundle, status), [bundle, status]);

  if (!bundle) {
    return (
      <Card className="border-zinc-800 bg-zinc-950/40 p-6">
        <p className="text-sm text-zinc-500">
          No pipeline bundle on this record yet (run may have failed or predates structured storage).
        </p>
      </Card>
    );
  }

  const log = bundle.log_intelligence as Record<string, unknown> | undefined;
  const risk = bundle.risk as Record<string, unknown> | undefined;
  const retrieval = bundle.retrieval as Record<string, unknown> | undefined;
  const obl = bundle.obligations as Record<string, unknown> | undefined;
  const esc = bundle.escalation as Record<string, unknown> | undefined;
  const critic = bundle.critic as Record<string, unknown> | undefined;
  const jurs = bundle.jurisdictions;

  const citations = retrieval?.regulatory_citations;
  const citationCount = Array.isArray(citations) ? citations.length : 0;
  const matrix = obl?.obligation_matrix;
  const criticPassed = critic?.passed === true;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-zinc-800/90 pb-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-zinc-100">Case report</h2>
          <p className="mt-1 font-mono text-[11px] text-zinc-500">{incidentId}</p>
          {Array.isArray(jurs) && jurs.length > 0 && (
            <p className="mt-2 text-xs text-zinc-400">
              <span className="text-zinc-500">Jurisdictions scoped: </span>
              {jurs.join(", ")}
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone={status === "completed" ? "ok" : status === "needs_review" ? "warn" : "neutral"}>
            {status}
          </Badge>
          {critic != null && (
            <Badge tone={criticPassed ? "ok" : "warn"}>
              Critic {criticPassed ? "passed" : "needs review"}
            </Badge>
          )}
        </div>
      </div>

      <section className="rounded-xl border border-zinc-800/90 bg-zinc-900/30 p-4">
        <h3 className="text-xs font-semibold uppercase tracking-[0.15em] text-zinc-500">Case snapshot</h3>
        <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs text-zinc-500">Incident type</dt>
            <dd className="text-zinc-200">{str(log?.incident_type)}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">Severity (model)</dt>
            <dd className="text-zinc-200">{str(log?.severity_hint)}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">Records exposed</dt>
            <dd className="font-mono text-zinc-200">{num(log?.records_exposed)}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">Personal data</dt>
            <dd className="text-zinc-200">{boolYesNo(log?.personal_data_involved)}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-xs text-zinc-500">Timeline / attack vector</dt>
            <dd className="text-zinc-300">{str(log?.timeline)} · {str(log?.attack_vector)}</dd>
          </div>
        </dl>
      </section>

      <section className="rounded-xl border border-zinc-800/90 bg-zinc-900/30 p-4">
        <h3 className="text-xs font-semibold uppercase tracking-[0.15em] text-zinc-500">Risk scoring</h3>
        <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <dt className="text-xs text-zinc-500">Severity score</dt>
            <dd className="font-mono text-lg text-emerald-200/95">{num(risk?.severity_score)}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">Regulatory exposure</dt>
            <dd className="font-mono text-zinc-200">{num(risk?.regulatory_exposure_score)}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">Operational impact</dt>
            <dd className="font-mono text-zinc-200">{num(risk?.operational_impact_score)}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">Confidence</dt>
            <dd className="font-mono text-zinc-200">{num(risk?.confidence_level)}</dd>
          </div>
        </dl>
        {risk?.rationale != null && typeof risk.rationale === "string" && risk.rationale.trim() && (
          <p className="mt-4 text-sm leading-relaxed text-zinc-300">{risk.rationale}</p>
        )}
      </section>

      <section className="rounded-xl border border-zinc-800/90 bg-zinc-900/30 p-4">
        <h3 className="text-xs font-semibold uppercase tracking-[0.15em] text-zinc-500">
          Regulatory obligations
        </h3>
        <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs text-zinc-500">Authority notification</dt>
            <dd className="text-zinc-200">{boolYesNo(obl?.authority_notification_required)}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">Authority deadline (hours)</dt>
            <dd className="font-mono text-zinc-200">{num(obl?.authority_deadline_hours)}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">User / customer notification</dt>
            <dd className="text-zinc-200">{boolYesNo(obl?.user_notification_required)}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">Board escalation</dt>
            <dd className="text-zinc-200">{boolYesNo(obl?.board_escalation_required)}</dd>
          </div>
        </dl>
        {deadlineAt && (
          <p className="mt-3 text-xs text-zinc-500">
            Stored deadline target: <span className="font-mono text-zinc-400">{deadlineAt}</span>
          </p>
        )}
        {Array.isArray(matrix) &&
          matrix.length > 0 &&
          typeof matrix[0] === "object" &&
          matrix[0] !== null && (
          <div className="mt-4 overflow-x-auto">
            <p className="mb-2 text-xs font-medium text-zinc-500">Obligation matrix</p>
            <table className="w-full min-w-[480px] border-collapse text-left text-xs">
              <thead>
                <tr className="border-b border-zinc-800 text-zinc-500">
                  {Object.keys(matrix[0] as object).map((k) => (
                    <th key={k} className="py-2 pr-3 font-medium">
                      {k}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {matrix.map((row, i) => (
                  <tr key={i} className="border-b border-zinc-800/80 text-zinc-300">
                    {typeof row === "object" && row !== null
                      ? Object.values(row as Record<string, unknown>).map((cell, j) => (
                          <td key={j} className="py-2 pr-3 align-top">
                            {typeof cell === "object" ? JSON.stringify(cell) : String(cell ?? "—")}
                          </td>
                        ))
                      : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-xl border border-zinc-800/90 bg-zinc-900/30 p-4">
        <h3 className="text-xs font-semibold uppercase tracking-[0.15em] text-zinc-500">
          Retrieval summary
        </h3>
        <p className="mt-2 text-sm text-zinc-400">
          <span className="text-zinc-500">Primary query: </span>
          {str(retrieval?.query_used)}
        </p>
        <p className="mt-1 text-sm text-zinc-400">
          <span className="text-zinc-500">Jurisdiction focus (agent): </span>
          {str(retrieval?.jurisdiction_focus)} ·{" "}
          <span className="text-zinc-500">Citations retrieved: </span>
          {citationCount}
        </p>
      </section>

      <section className="rounded-xl border border-zinc-800/90 bg-zinc-900/30 p-4">
        <h3 className="text-xs font-semibold uppercase tracking-[0.15em] text-zinc-500">
          Escalation decision
        </h3>
        <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs text-zinc-500">Level</dt>
            <dd className="text-zinc-100">{str(esc?.level).replace(/_/g, " ")}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">Countdown (hours)</dt>
            <dd className="font-mono text-zinc-200">{num(esc?.countdown_hours)}</dd>
          </div>
        </dl>
        {esc?.rationale != null && typeof esc.rationale === "string" && esc.rationale.trim() && (
          <p className="mt-4 text-sm leading-relaxed text-zinc-300">{esc.rationale}</p>
        )}
        {Array.isArray(esc?.documentation_checklist) && esc.documentation_checklist.length > 0 && (
          <ul className="mt-4 list-inside list-disc space-y-1 text-sm text-zinc-300">
            {(esc.documentation_checklist as string[]).map((x, i) => (
              <li key={i}>{x}</li>
            ))}
          </ul>
        )}
      </section>

      {critic != null && (
        <section className="rounded-xl border border-zinc-800/90 bg-zinc-900/30 p-4">
          <h3 className="text-xs font-semibold uppercase tracking-[0.15em] text-zinc-500">
            Critic (quality gate)
          </h3>
          <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <dt className="text-xs text-zinc-500">Hallucination risk</dt>
              <dd className="font-mono text-zinc-200">{num(critic?.hallucination_risk)}</dd>
            </div>
            <div>
              <dt className="text-xs text-zinc-500">Citation accuracy</dt>
              <dd className="font-mono text-zinc-200">{num(critic?.citation_accuracy_score)}</dd>
            </div>
            <div>
              <dt className="text-xs text-zinc-500">Reasoning</dt>
              <dd className="font-mono text-zinc-200">{num(critic?.reasoning_score)}</dd>
            </div>
            <div>
              <dt className="text-xs text-zinc-500">Escalation fit</dt>
              <dd className="font-mono text-zinc-200">{num(critic?.escalation_correctness_score)}</dd>
            </div>
          </dl>
        </section>
      )}

      <section className="rounded-xl border border-emerald-900/40 bg-emerald-950/20 p-4">
        <h3 className="text-xs font-semibold uppercase tracking-[0.15em] text-emerald-400/90">
          What to do next
        </h3>
        <ol className="mt-3 list-inside list-decimal space-y-2 text-sm leading-relaxed text-zinc-200">
          {nextSteps.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ol>
        <p className="mt-4 text-xs leading-relaxed text-zinc-500">
          This report is decision-support only — validate all regulatory duties and deadlines with qualified
          counsel before filings or external statements.
        </p>
      </section>
    </div>
  );
}
