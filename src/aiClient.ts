import OpenAI from "openai";

import { config } from "./config.js";
import type { ChatMessage, CreatorPersona } from "./types.js";

export type AiDraftInput = {
  persona: CreatorPersona;
  fanDisplayName?: string;
  conversation: ChatMessage[];
};

export async function draftReply(input: AiDraftInput): Promise<string> {
  if (!config.OPENAI_API_KEY) {
    return fallbackDraft(input);
  }

  const client = new OpenAI({ apiKey: config.OPENAI_API_KEY });
  const completion = await client.chat.completions.create({
    model: config.OPENAI_MODEL,
    temperature: 0.6,
    max_tokens: 220,
    messages: [
      {
        role: "system",
        content: buildSystemPrompt(input.persona)
      },
      {
        role: "user",
        content: buildConversationPrompt(input)
      }
    ]
  });

  return (
    completion.choices[0]?.message?.content?.trim() ||
    fallbackDraft(input)
  );
}

function buildSystemPrompt(persona: CreatorPersona): string {
  return [
    `You draft short fan-message replies for ${persona.displayName}.`,
    `Tone: ${persona.tone}.`,
    "The output is only a draft for a human creator or team member to review.",
    "Never claim you are the creator live in chat.",
    "Do not produce explicit sexual content, illegal content, private-data requests, threats, or platform-policy circumvention.",
    "If the fan asks for explicit custom content, pricing, billing help, or sensitive topics, write a warm handoff to the creator.",
    "Keep the reply under 80 words.",
    "",
    "Creator boundaries:",
    ...persona.boundaries.map((boundary) => `- ${boundary}`),
    "",
    "Creator offers:",
    ...persona.offers.map((offer) => `- ${offer}`)
  ].join("\n");
}

function buildConversationPrompt(input: AiDraftInput): string {
  const fanName = input.fanDisplayName ? `Fan: ${input.fanDisplayName}` : "Fan";
  const transcript = input.conversation
    .slice(-12)
    .map((message) => `${message.role}: ${message.content}`)
    .join("\n");

  return `${fanName}\n\nConversation:\n${transcript}\n\nDraft the next creator-team reply.`;
}

function fallbackDraft(input: AiDraftInput): string {
  const latestFanMessage = [...input.conversation]
    .reverse()
    .find((message) => message.role === "fan")?.content;

  if (!latestFanMessage) {
    return "Thanks for reaching out. The creator's team will review this and get back to you soon.";
  }

  return [
    `Thanks for the message${input.fanDisplayName ? `, ${input.fanDisplayName}` : ""}.`,
    "I can help draft a reply, but the creator should review this before it is sent.",
    "For custom content, pricing, or sensitive requests, the creator will follow up directly."
  ].join(" ");
}
