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
  jurisdiction_hint: string;
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
