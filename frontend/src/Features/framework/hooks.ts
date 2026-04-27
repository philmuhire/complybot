"use client";

import { useAuth } from "@clerk/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";

import { createAuthedClient } from "@/shared/api/authed-client";

import { frameworkApi, jurisdictionHintsApi } from "./api";
import type { FrameworkIngest } from "./framework.types";

export function useFrameworkApi() {
  const { getToken } = useAuth();
  const client = useMemo(
    () => createAuthedClient(() => getToken()),
    [getToken],
  );
  return useMemo(() => frameworkApi(client), [client]);
}

export function useJurisdictionHints() {
  const { getToken } = useAuth();
  const client = useMemo(
    () => createAuthedClient(() => getToken()),
    [getToken],
  );
  return useQuery({
    queryKey: ["jurisdiction-hints"],
    queryFn: async () => (await jurisdictionHintsApi(client).list()).data.items,
  });
}

export function useFrameworkList() {
  const api = useFrameworkApi();
  return useQuery({
    queryKey: ["framework-documents"],
    queryFn: async () => (await api.list()).data,
  });
}

export function useFrameworkIngest() {
  const api = useFrameworkApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: FrameworkIngest) => api.ingest(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["framework-documents"] });
      void qc.invalidateQueries({ queryKey: ["jurisdiction-hints"] });
    },
  });
}

export function useFrameworkUpload() {
  const api = useFrameworkApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: FormData) => api.upload(form),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["framework-documents"] });
      void qc.invalidateQueries({ queryKey: ["jurisdiction-hints"] });
    },
  });
}

export function useFrameworkDelete() {
  const api = useFrameworkApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.remove(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["framework-documents"] });
    },
  });
}
