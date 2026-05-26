export type ChatRole = "fan" | "creator" | "assistant";

export type ChatMessage = {
  role: ChatRole;
  content: string;
  createdAt?: string;
};

export type CreatorPersona = {
  displayName: string;
  tone: "friendly" | "flirty" | "luxury" | "playful" | "professional";
  boundaries: string[];
  offers: string[];
  disclosure: string;
};

export type FanProfile = {
  platformUserId: string;
  displayName?: string;
  isAgeVerified: boolean;
  consentedToAiAssistant: boolean;
};

export type SafetyDecision = "allow" | "block" | "needs_human_review";

export type SafetyResult = {
  decision: SafetyDecision;
  reasons: string[];
  matchedRules: string[];
};

export type ChatSuggestionRequest = {
  creatorId: string;
  fan: FanProfile;
  conversation: ChatMessage[];
  persona?: Partial<CreatorPersona>;
};

export type ChatSuggestionResponse = {
  requestId: string;
  status: "suggested" | "blocked" | "needs_human_review";
  disclosure: string;
  reply?: string;
  safety: SafetyResult;
  shouldSendAutomatically: false;
};
