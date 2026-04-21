import { z } from "zod";

export const analyzeBodySchema = z.object({
  raw_input: z.string().min(20, "Provide enough incident detail for the engine."),
  jurisdiction_hint: z.enum(["EU", "US-FED", "UK", "OTHER"]).default("EU"),
});

export type AnalyzeBodyInput = z.infer<typeof analyzeBodySchema>;
