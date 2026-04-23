import type { AxiosInstance } from "axios";

import type { FrameworkIngest, FrameworkDocument } from "./framework.types";

export function frameworkApi(client: AxiosInstance) {
  return {
    list: () => client.get<{ items: FrameworkDocument[] }>("/api/framework-documents"),
    ingest: (body: FrameworkIngest) => client.post("/api/framework-documents", body),
    upload: (form: FormData) =>
      client.post<unknown>("/api/framework-documents/upload", form),
    remove: (userDocumentId: string) =>
      client.delete<{ ok: boolean; deleted: number }>(
        `/api/framework-documents/${userDocumentId}`,
      ),
  };
}
