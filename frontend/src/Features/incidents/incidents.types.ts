export type IncidentSummary = {
  id: string;
  created_at: string | null;
  incident_type: string | null;
  severity_score: number | null;
  escalation_level: string | null;
  status: string;
  regulator_notification_required: boolean | null;
};

export type AnalyzePayload = {
  raw_input: string;
  jurisdictions: string[];
};

/** Nested under `incident.final_report` from the API; mirrors backend pipeline bundle. */
export type PipelineBundle = {
  jurisdictions?: string[];
  jurisdiction_hint?: string;
  log_intelligence?: Record<string, unknown>;
  retrieval?: Record<string, unknown>;
  risk?: Record<string, unknown>;
  obligations?: Record<string, unknown>;
  escalation?: Record<string, unknown>;
  critic?: Record<string, unknown>;
};

export type IncidentDetailResponse = {
  incident: {
    id: string;
    created_at: string | null;
    status: string;
    raw_input: string;
    final_report: unknown;
    severity_score: number | null;
    escalation_level: string | null;
    regulator_notification_required: boolean | null;
    deadline_at: string | null;
    confidence_score: number | null;
  };
  traces: {
    agent_name: string;
    latency_ms: number | null;
    output_summary: string;
    created_at: string | null;
  }[];
};
