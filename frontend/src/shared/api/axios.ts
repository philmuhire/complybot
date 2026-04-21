import Axios from "axios";

const baseURL =
  typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
    : process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const axiosBase = Axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});
