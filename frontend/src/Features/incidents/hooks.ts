"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";

import { createAuthedClient } from "@/shared/api/authed-client";

import { incidentsApi } from "./api";

export function useIncidentsApi() {
  const { getToken } = useAuth();
  const client = useMemo(() => createAuthedClient(() => getToken()), [getToken]);
  return useMemo(() => incidentsApi(client), [client]);
}

export function useIncidentList() {
  const api = useIncidentsApi();
  return useQuery({
    queryKey: ["incidents"],
    queryFn: async () => {
      const res = await api.list();
      return res.data;
    },
  });
}

export function useIncidentDetail(id: string | null) {
  const api = useIncidentsApi();
  return useQuery({
    queryKey: ["incident", id],
    enabled: !!id,
    queryFn: async () => {
      const res = await api.get(id!);
      return res.data;
    },
  });
}

export function useAnalyzeIncident() {
  const api = useIncidentsApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { raw_input: string; jurisdiction_hint: string }) => {
      const res = await api.analyze(vars);
      return res.data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["incidents"] });
    },
  });
}
