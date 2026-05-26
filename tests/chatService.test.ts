import { describe, expect, it } from "vitest";

import { createChatSuggestion } from "../src/chatService.js";
import type { ChatSuggestionRequest } from "../src/types.js";

const baseRequest: ChatSuggestionRequest = {
  creatorId: "creator_123",
  fan: {
    platformUserId: "fan_123",
    displayName: "Sam",
    isAgeVerified: true,
    consentedToAiAssistant: true
  },
  conversation: [
    {
      role: "fan",
      content: "Your latest post was great. Anything new coming today?"
    }
  ]
};

describe("createChatSuggestion", () => {
  it("returns a draft suggestion for safe requests", async () => {
    const result = await createChatSuggestion(baseRequest);

    expect(result.status).toBe("suggested");
    expect(result.reply).toContain("Thanks for the message");
    expect(result.shouldSendAutomatically).toBe(false);
  });

  it("does not generate a reply for blocked requests", async () => {
    const result = await createChatSuggestion({
      ...baseRequest,
      fan: { ...baseRequest.fan, consentedToAiAssistant: false }
    });

    expect(result.status).toBe("blocked");
    expect(result.reply).toBeUndefined();
    expect(result.shouldSendAutomatically).toBe(false);
  });

  it("uses configured persona disclosure", async () => {
    const result = await createChatSuggestion({
      ...baseRequest,
      persona: {
        displayName: "Maya",
        tone: "playful",
        disclosure: "AI draft. Human review required."
      }
    });

    expect(result.disclosure).toBe("AI draft. Human review required.");
  });
});
