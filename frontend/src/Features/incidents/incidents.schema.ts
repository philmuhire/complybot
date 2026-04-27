import { z } from "zod";

export const analyzeBodySchema = z.object({
  raw_input: z.string().min(20, "Provide enough incident detail for the engine."),
  jurisdictions: z
    .array(z.string().min(1).max(128))
    .min(1, "Select at least one jurisdiction tag from the regulations list above."),
});

export type AnalyzeBodyInput = z.infer<typeof analyzeBodySchema>;
