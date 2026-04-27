"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { useJurisdictionHints } from "@/Features/framework/hooks";
import { analyzeBodySchema } from "@/Features/incidents/incidents.schema";
import { Badge } from "@/shared/components/ui/Badge";
import { Button } from "@/shared/components/ui/Button";
import { Card } from "@/shared/components/ui/Card";
import { Textarea } from "@/shared/components/ui/Textarea";
import { Spinner } from "@/shared/components/feedback/Spinner";

import {
  CaseReport,
  extractPipelineBundle,
  pipelineBundleFromAnalyze,
} from "./CaseReport";
import {
  useAnalyzeIncident,
  useIncidentDetail,
  useIncidentList,
} from "./hooks";

function JsonPane({ value }: { value: unknown }) {
  const txt = JSON.stringify(value, null, 2);
  return (
    <pre className="max-h-[480px] overflow-auto rounded-lg border border-zinc-800 bg-black/40 p-4 font-mono text-[11px] leading-relaxed text-emerald-100/90">
      {txt}
    </pre>
  );
}

export function IncidentGovernance() {
  const [input, setInput] = useState("");
  const [jurSelected, setJurSelected] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const jursInitialized = useRef(false);
  const jurisdictionHints = useJurisdictionHints();

  const list = useIncidentList();
  const detail = useIncidentDetail(selectedId);
  const analyze = useAnalyzeIncident();

  useEffect(() => {
    if (jursInitialized.current || jurisdictionHints.isLoading) return;
    if (!jurisdictionHints.isFetched) return;
    jursInitialized.current = true;
    const d = jurisdictionHints.data;
    if (d?.length) {
      setJurSelected(d.includes("EU") ? ["EU"] : [d[0]]);
    } else {
      setJurSelected([]);
    }
  }, [jurisdictionHints.data, jurisdictionHints.isFetched, jurisdictionHints.isLoading]);

  const parsed = useMemo(
    () => analyzeBodySchema.safeParse({ raw_input: input, jurisdictions: jurSelected }),
    [input, jurSelected],
  );

  const toggleJurHint = (h: string) => {
    setJurSelected((s) => {
      const on = s.some((x) => x.toLowerCase() === h.toLowerCase());
      if (on) {
        const next = s.filter((x) => x.toLowerCase() !== h.toLowerCase());
        return next.length ? next : s;
      }
      return [...s, h];
    });
  };

  const run = () => {
    const r = analyzeBodySchema.safeParse({ raw_input: input, jurisdictions: jurSelected });
    if (!r.success) return;
    analyze.mutate(
      { raw_input: r.data.raw_input, jurisdictions: r.data.jurisdictions },
      {
        onSuccess: (data: unknown) => {
          const d = data as { incident_id?: string };
          if (d?.incident_id) setSelectedId(d.incident_id);
        },
      },
    );
  };

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-50 md:text-3xl">
          Compliance governance engine
        </h1>
        <p className="max-w-3xl text-sm leading-relaxed text-zinc-400">
          Submit security logs or incident narratives. The orchestrator routes through Log
          Intelligence → RAG retrieval → Risk → Obligations → Escalation → Critic, with MCP tools
          for traceable actions — not a chatbot.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <Badge tone="ok">Step 1</Badge>
            <span className="text-sm font-medium text-zinc-200">Incident intake</span>
          </div>
          <label className="mb-2 block text-xs uppercase tracking-wide text-zinc-500">
            Raw logs / narrative
          </label>
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Paste IAM trails, IDS alerts, ticket narrative, approximate record counts..."
          />
          <div className="mt-4 space-y-3">
            <div>
              <span className="mb-1 block text-xs uppercase tracking-wide text-zinc-500">
                Jurisdictions
              </span>
              <p className="mb-2 text-xs text-zinc-500">
                Select one or more tags that already exist on regulation rows in the database.
                Framework uploads and seeds define which labels appear here.
              </p>
              {jurisdictionHints.isLoading && (
                <p className="text-xs text-zinc-500">Loading jurisdiction tags from regulations…</p>
              )}
              {jurisdictionHints.isFetched &&
                jurisdictionHints.data &&
                jurisdictionHints.data.length === 0 && (
                  <p className="rounded-lg border border-amber-500/30 bg-amber-950/25 px-3 py-2 text-xs text-amber-200/90">
                    No jurisdiction tags in the regulations index yet. Seed the database or add a
                    framework document with jurisdictions before running the pipeline.
                  </p>
                )}
              {jurisdictionHints.data && jurisdictionHints.data.length > 0 && (
                <div className="max-h-32 overflow-y-auto rounded-lg border border-zinc-800/80 bg-zinc-900/40 p-3">
                  <p className="mb-2 text-[10px] font-medium uppercase tracking-wider text-zinc-500">
                    Distinct values from regulations
                  </p>
                  <div className="flex flex-wrap gap-x-4 gap-y-2">
                    {jurisdictionHints.data.map((h) => {
                      const on = jurSelected.some(
                        (x) => x.toLowerCase() === h.toLowerCase(),
                      );
                      return (
                        <label
                          key={h}
                          className="flex cursor-pointer items-center gap-2 text-xs text-zinc-300"
                        >
                          <input
                            type="checkbox"
                            className="rounded border-zinc-600"
                            checked={on}
                            onChange={() => toggleJurHint(h)}
                          />
                          {h}
                        </label>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
            <Button
              className="w-full sm:max-w-xs"
              disabled={!parsed.success || analyze.isPending}
              onClick={run}
            >
              Run governance pipeline
            </Button>
          </div>
          {!parsed.success && input.length > 0 && (
            <p className="mt-2 text-xs text-rose-400">
              {parsed.error.issues[0]?.message}
            </p>
          )}
          {analyze.isPending && (
            <div className="mt-4">
              <Spinner label="Agents executing with MCP tools — may take a minute" />
            </div>
          )}
          {analyze.isError && (
            <p className="mt-4 text-sm text-rose-400">
              {(analyze.error as Error).message}
            </p>
          )}
          {analyze.isSuccess && analyze.data && (
            <div className="mt-4 space-y-4">
              <Badge tone="ok">Completed</Badge>
              <CaseReport
                bundle={pipelineBundleFromAnalyze(analyze.data)}
                incidentId={
                  (analyze.data as { incident_id?: string }).incident_id ?? ""
                }
                status={
                  (analyze.data as { pipeline?: { critic?: { passed?: boolean } } })
                    .pipeline?.critic?.passed === false
                    ? "needs_review"
                    : "completed"
                }
                deadlineAt={null}
              />
              <details className="group rounded-lg border border-zinc-800 bg-zinc-950/40">
                <summary className="cursor-pointer select-none px-3 py-2 text-xs text-zinc-500 hover:text-zinc-400">
                  Raw pipeline JSON
                </summary>
                <div className="border-t border-zinc-800 p-2">
                  <JsonPane value={analyze.data} />
                </div>
              </details>
            </div>
          )}
        </Card>

        <Card>
          <div className="mb-4 flex items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="neutral">Registry</Badge>
              <span className="text-sm font-medium text-zinc-200">Stored cases</span>
            </div>
            <Button
              variant="ghost"
              className="text-xs"
              onClick={() => list.refetch()}
              disabled={list.isFetching}
            >
              Refresh
            </Button>
          </div>
          {list.isLoading && <Spinner label="Loading incidents" />}
          {list.data && (
            <div className="max-h-[420px] space-y-2 overflow-auto pr-1">
              {list.data.length === 0 && (
                <p className="text-sm text-zinc-500">No incidents yet.</p>
              )}
              {list.data.map((row) => (
                <button
                  key={row.id}
                  type="button"
                  onClick={() => setSelectedId(row.id)}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition hover:bg-zinc-900 ${
                    selectedId === row.id
                      ? "border-emerald-600/80 bg-emerald-950/40"
                      : "border-zinc-800 bg-zinc-950/60"
                  }`}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-[11px] text-zinc-500">{row.id.slice(0, 8)}…</span>
                    <Badge tone={row.regulator_notification_required ? "warn" : "neutral"}>
                      {row.incident_type ?? "pending"}
                    </Badge>
                    <span className="text-xs text-zinc-500">{row.status}</span>
                  </div>
                  <div className="mt-1 text-xs text-zinc-400">
                    Sev {row.severity_score ?? "—"} · Esc {row.escalation_level ?? "—"}
                  </div>
                </button>
              ))}
            </div>
          )}
        </Card>
      </div>

      {selectedId && (
        <div className="flex flex-col gap-6">
          {detail.isLoading && <Spinner label="Loading case detail" />}
          {detail.data && (
            <>
              <Card className="p-6">
                <div className="mb-6 flex flex-wrap items-center gap-2">
                  <Badge tone="ok">Case summary</Badge>
                  <span className="text-sm font-medium text-zinc-200">
                    Structured report for selected incident
                  </span>
                </div>
                <CaseReport
                  bundle={extractPipelineBundle(detail.data.incident.final_report)}
                  incidentId={detail.data.incident.id}
                  status={detail.data.incident.status}
                  deadlineAt={detail.data.incident.deadline_at}
                />
              </Card>

              <Card>
                <div className="mb-4 flex flex-wrap items-center gap-2">
                  <Badge tone="warn">Traceability</Badge>
                  <span className="text-sm font-medium text-zinc-200">
                    Raw record &amp; agent traces
                  </span>
                </div>
                <div className="grid gap-6 lg:grid-cols-2">
                  <div>
                    <h3 className="mb-2 text-xs uppercase tracking-wide text-zinc-500">
                      Incident record
                    </h3>
                    <JsonPane value={detail.data.incident} />
                  </div>
                  <div>
                    <h3 className="mb-2 text-xs uppercase tracking-wide text-zinc-500">
                      Agent traces
                    </h3>
                    <div className="max-h-[420px] space-y-3 overflow-auto">
                      {detail.data.traces.map((t) => (
                        <div
                          key={`${t.agent_name}-${t.created_at}`}
                          className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3 text-xs"
                        >
                          <div className="flex justify-between gap-2 text-[11px] text-zinc-400">
                            <span className="font-semibold text-emerald-300">{t.agent_name}</span>
                            <span>{t.latency_ms?.toFixed?.(0) ?? "—"} ms</span>
                          </div>
                          <p className="mt-2 line-clamp-6 whitespace-pre-wrap font-mono text-[10px] text-zinc-400">
                            {t.output_summary}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            </>
          )}
        </div>
      )}
    </div>
  );
}
