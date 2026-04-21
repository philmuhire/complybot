import type { AxiosInstance } from "axios";

import type {
  AnalyzePayload,
  IncidentDetailResponse,
  IncidentSummary,
} from "./incidents.types";

export function incidentsApi(client: AxiosInstance) {
  return {
    list: () => client.get<IncidentSummary[]>("/api/incidents"),
    get: (id: string) => client.get<IncidentDetailResponse>(`/api/incidents/${id}`),
    analyze: (body: AnalyzePayload) =>
      client.post("/api/incidents/analyze", body),
  };
}
