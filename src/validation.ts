import { z } from "zod";

export const chatSuggestionRequestSchema = z.object({
  creatorId: z.string().min(1).max(128),
  fan: z.object({
    platformUserId: z.string().min(1).max(256),
    displayName: z.string().max(256).optional(),
    isAgeVerified: z.boolean(),
    consentedToAiAssistant: z.boolean()
  }),
  conversation: z
    .array(
      z.object({
        role: z.enum(["fan", "creator", "assistant"]),
        content: z.string().min(1).max(4000),
        createdAt: z.string().datetime().optional()
      })
    )
    .min(1)
    .max(50),
  persona: z
    .object({
      displayName: z.string().min(1).max(128).optional(),
      tone: z
        .enum(["friendly", "flirty", "luxury", "playful", "professional"])
        .optional(),
      boundaries: z.array(z.string().min(1).max(500)).max(20).optional(),
      offers: z.array(z.string().min(1).max(500)).max(20).optional(),
      disclosure: z.string().min(1).max(500).optional()
    })
    .optional()
});
