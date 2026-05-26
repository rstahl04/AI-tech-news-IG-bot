import type { ChatMessage, FanProfile, SafetyResult } from "./types.js";

type SafetyRule = {
  id: string;
  decision: SafetyResult["decision"];
  reason: string;
  pattern: RegExp;
};

const blockingRules: SafetyRule[] = [
  {
    id: "minor-sexual-content",
    decision: "block",
    reason: "References to minors or underage sexual content are not allowed.",
    pattern:
      /\b(under\s*18|underage|minor|child|kid|teen(?:ager)?|schoolgirl|schoolboy|jailbait|little\s+girl|little\s+boy)\b/i
  },
  {
    id: "non-consensual-content",
    decision: "block",
    reason: "Non-consensual, coercive, or exploitative content is not allowed.",
    pattern:
      /\b(non[-\s]?consensual|without\s+(?:her|his|their)\s+consent|rape|forced|drugged|unconscious|blackmail|extort)\b/i
  },
  {
    id: "doxxing-or-private-data",
    decision: "block",
    reason: "Requests for private personal data or doxxing are not allowed.",
    pattern:
      /\b(home\s+address|real\s+address|doxx|dox|social\s+security|passport|driver'?s\s+license|bank\s+account)\b/i
  }
];

const humanReviewRules: SafetyRule[] = [
  {
    id: "explicit-sexual-request",
    decision: "needs_human_review",
    reason: "Explicit sexual requests should be reviewed and answered by the creator.",
    pattern:
      /\b(nude|nudes|explicit|sex|sext|sexting|orgasm|cum|fetish|custom\s+video|custom\s+content|roleplay|dick|pussy|boobs?)\b/i
  },
  {
    id: "payments-or-refunds",
    decision: "needs_human_review",
    reason: "Billing, refund, tip, and custom-price conversations need human confirmation.",
    pattern:
      /\b(refund|chargeback|tip|tips|price|pricing|discount|bundle|payment|paid|custom\s+price)\b/i
  },
  {
    id: "platform-circumvention",
    decision: "needs_human_review",
    reason: "Requests to move transactions or content off-platform need policy review.",
    pattern:
      /\b(cashapp|venmo|paypal|telegram|snapchat|whatsapp|off[-\s]?platform|outside\s+onlyfans|outside\s+of)\b/i
  }
];

export function evaluateSafety(
  fan: FanProfile,
  conversation: ChatMessage[]
): SafetyResult {
  const reasons: string[] = [];
  const matchedRules: string[] = [];

  if (!fan.isAgeVerified) {
    reasons.push("Fan must be age-verified before receiving AI-assisted replies.");
    matchedRules.push("age-verification-required");
  }

  if (!fan.consentedToAiAssistant) {
    reasons.push("Fan must consent to AI-assisted messaging or disclosure workflow.");
    matchedRules.push("ai-consent-required");
  }

  const text = conversation.map((message) => message.content).join("\n");

  for (const rule of blockingRules) {
    if (rule.pattern.test(text)) {
      reasons.push(rule.reason);
      matchedRules.push(rule.id);
    }
  }

  if (matchedRules.length > 0) {
    return {
      decision: "block",
      reasons,
      matchedRules
    };
  }

  for (const rule of humanReviewRules) {
    if (rule.pattern.test(text)) {
      reasons.push(rule.reason);
      matchedRules.push(rule.id);
    }
  }

  if (matchedRules.length > 0) {
    return {
      decision: "needs_human_review",
      reasons,
      matchedRules
    };
  }

  return {
    decision: "allow",
    reasons: ["Conversation passed baseline safety checks."],
    matchedRules: []
  };
}
