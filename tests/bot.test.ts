import { describe, expect, it } from "vitest";
import { DmBot } from "../src/bot.js";
import { InMemoryConversationStore } from "../src/state.js";
import type { AppConfig } from "../src/config.js";
import type { IncomingMessage } from "../src/types.js";

const baseConfig = {
  PORT: 3000,
  BOT_NAME: "Test Bot",
  BOT_TOPIC: "AI tech",
  BOT_DAILY_MESSAGE_LIMIT: 2,
  BOT_REPLY_COOLDOWN_SECONDS: 30,
  TWITTER_API_BASE_URL: "https://api.x.com"
} as AppConfig;

describe("DmBot", () => {
  it("requires opt-in before sending topic replies", () => {
    const bot = new DmBot(new InMemoryConversationStore(), baseConfig);
    const decision = bot.decide(message("latest"));

    expect(decision.reason).toBe("requires_opt_in");
    expect(decision.reply).toContain("SUBSCRIBE");
  });

  it("subscribes a user and returns the latest digest after cooldown", () => {
    const bot = new DmBot(new InMemoryConversationStore(), baseConfig);

    expect(bot.decide(message("subscribe")).reason).toBe("user_subscribed");

    const decision = bot.decide(message("latest", new Date("2026-06-21T00:01:00.000Z")));

    expect(decision.reason).toBe("latest_requested");
    expect(decision.reply).toContain("AI tech digest");
  });

  it("does not reply during the cooldown window", () => {
    const bot = new DmBot(new InMemoryConversationStore(), baseConfig);

    bot.decide(message("subscribe"));
    const decision = bot.decide(message("latest", new Date("2026-06-21T00:00:05.000Z")));

    expect(decision).toEqual({
      reason: "cooldown_active"
    });
  });

  it("unsubscribes users on stop commands", () => {
    const bot = new DmBot(new InMemoryConversationStore(), baseConfig);

    bot.decide(message("subscribe"));
    const stopDecision = bot.decide(message("stop", new Date("2026-06-21T00:01:00.000Z")));
    const laterDecision = bot.decide(message("latest", new Date("2026-06-21T00:02:00.000Z")));

    expect(stopDecision.reason).toBe("user_unsubscribed");
    expect(laterDecision.reason).toBe("requires_opt_in");
  });

  it("caps replies by daily limit", () => {
    const bot = new DmBot(new InMemoryConversationStore(), {
      ...baseConfig,
      BOT_DAILY_MESSAGE_LIMIT: 1,
      BOT_REPLY_COOLDOWN_SECONDS: 0
    });

    bot.decide(message("subscribe"));
    const decision = bot.decide(message("latest", new Date("2026-06-21T00:01:00.000Z")));

    expect(decision.reason).toBe("daily_limit_reached");
  });
});

function message(text: string, timestamp = new Date("2026-06-21T00:00:00.000Z")): IncomingMessage {
  return {
    id: `message:${text}:${timestamp.toISOString()}`,
    platform: "instagram",
    senderId: "user-1",
    recipientId: "bot-1",
    text,
    timestamp,
    raw: {}
  };
}
