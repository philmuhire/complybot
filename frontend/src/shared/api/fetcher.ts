import type { AxiosInstance } from "axios";

export async function fetcher<T>(
  client: AxiosInstance,
  url: string,
): Promise<T> {
  const res = await client.get<T>(url);
  return res.data;
}
