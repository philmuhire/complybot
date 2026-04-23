"use client";

import Axios, { type AxiosInstance } from "axios";

export function createAuthedClient(getToken: () => Promise<string | null>): AxiosInstance {
  const client = Axios.create({
    baseURL:
      typeof window !== "undefined"
        ? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
        : process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
    headers: { "Content-Type": "application/json" },
  });
  client.interceptors.request.use(async (config) => {
    if (config.data instanceof FormData) {
      delete (config.headers as { "Content-Type"?: string })["Content-Type"];
    }
    const token = await getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
  return client;
}
