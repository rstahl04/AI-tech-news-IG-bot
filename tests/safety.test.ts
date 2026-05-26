import { describe, expect, it } from "vitest";

import { evaluateSafety } from "../src/safety.js";
import type { ChatMessage, FanProfile } from "../src/types.js";

const verifiedFan: FanProfile = {
  platformUserId: "fan_123",
  displayName: "Sam",
  isAgeVerified: true,
  consentedToAiAssistant: true
};

function conversation(content: string): ChatMessage[] {
  return [{ role: "fan", content }];
}

describe("evaluateSafety", () => {
  it("allows low-risk fan messages from verified consenting fans", () => {
    const result = evaluateSafety(
      verifiedFan,
      conversation("Loved your latest post. What are you sharing this week?")
    );

    expect(result.decision).toBe("allow");
    expect(result.matchedRules).toEqual([]);
  });

  it("blocks fans that are not age verified", () => {
    const result = evaluateSafety(
      { ...verifiedFan, isAgeVerified: false },
      conversation("Hi there")
    );

    expect(result.decision).toBe("block");
    expect(result.matchedRules).toContain("age-verification-required");
  });

  it("blocks coercive or underage content", () => {
    const result = evaluateSafety(
      verifiedFan,
      conversation("Can you make underage roleplay content?")
    );

    expect(result.decision).toBe("block");
    expect(result.matchedRules).toContain("minor-sexual-content");
  });

  it("routes explicit custom requests to human review", () => {
    const result = evaluateSafety(
      verifiedFan,
      conversation("How much for a custom video?")
    );

    expect(result.decision).toBe("needs_human_review");
    expect(result.matchedRules).toContain("explicit-sexual-request");
  });
});
