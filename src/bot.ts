import type { AppConfig } from "./config.js";
import type { ConversationStore, UserConversationState } from "./state.js";
import type { BotDecision, IncomingMessage } from "./types.js";

const START_COMMANDS = new Set(["start", "subscribe", "yes"]);
const STOP_COMMANDS = new Set(["stop", "unsubscribe", "cancel", "quit"]);
const HELP_COMMANDS = new Set(["help", "info", "?"]);
const LATEST_COMMANDS = new Set(["latest", "news", "update"]);

export class DmBot {
  constructor(
    private readonly store: ConversationStore,
    private readonly config: AppConfig
  ) {}

  decide(message: IncomingMessage): BotDecision {
    const text = normalize(message.text);
    const command = firstToken(text);
    const currentState = this.getCurrentState(message);

    if (STOP_COMMANDS.has(command)) {
      this.store.save(message.platform, message.senderId, {
        ...currentState,
        optedIn: false,
        stopped: true,
        updatedAt: message.timestamp
      });

      return {
        reply: "You are unsubscribed. I won't send more messages unless you reply SUBSCRIBE.",
        reason: "user_unsubscribed"
      };
    }

    if (START_COMMANDS.has(command)) {
      const nextState = this.incrementMessageCount(currentState, message.timestamp, {
        optedIn: true,
        stopped: false
      });
      this.store.save(message.platform, message.senderId, nextState);

      return {
        reply: `You're subscribed to ${this.config.BOT_TOPIC} updates from ${this.config.BOT_NAME}. Reply LATEST for today's digest or STOP anytime.`,
        reason: "user_subscribed"
      };
    }

    if (HELP_COMMANDS.has(command)) {
      return {
        reply: "Commands: SUBSCRIBE to opt in, LATEST for a digest, HELP for this menu, STOP to unsubscribe.",
        reason: "help_requested"
      };
    }

    if (!currentState.optedIn || currentState.stopped) {
      return {
        reply: `I only reply with ${this.config.BOT_TOPIC} updates after opt-in. Reply SUBSCRIBE to continue or STOP to block future replies.`,
        reason: "requires_opt_in"
      };
    }

    if (this.isCoolingDown(currentState, message.timestamp)) {
      return {
        reason: "cooldown_active"
      };
    }

    if (currentState.dailyMessageCount >= this.config.BOT_DAILY_MESSAGE_LIMIT) {
      return {
        reply: "You've reached today's message limit. Try again tomorrow, or reply STOP to unsubscribe.",
        reason: "daily_limit_reached"
      };
    }

    const nextState = this.incrementMessageCount(currentState, message.timestamp);
    this.store.save(message.platform, message.senderId, nextState);

    if (LATEST_COMMANDS.has(command)) {
      return {
        reply: buildDigest(this.config.BOT_TOPIC),
        reason: "latest_requested"
      };
    }

    return {
      reply: "I can help with AI tech updates. Reply LATEST for the digest, HELP for commands, or STOP to unsubscribe.",
      reason: "fallback"
    };
  }

  private getCurrentState(message: IncomingMessage): UserConversationState {
    const existing = this.store.get(message.platform, message.senderId);
    if (!existing) {
      return {
        dailyMessageCount: 0,
        optedIn: false,
        stopped: false,
        updatedAt: message.timestamp
      };
    }

    if (!isSameUtcDay(existing.updatedAt, message.timestamp)) {
      return {
        ...existing,
        dailyMessageCount: 0,
        updatedAt: message.timestamp
      };
    }

    return existing;
  }

  private incrementMessageCount(
    state: UserConversationState,
    timestamp: Date,
    overrides: Partial<UserConversationState> = {}
  ): UserConversationState {
    return {
      ...state,
      ...overrides,
      dailyMessageCount: state.dailyMessageCount + 1,
      lastMessageAt: timestamp,
      updatedAt: timestamp
    };
  }

  private isCoolingDown(state: UserConversationState, timestamp: Date): boolean {
    if (!state.lastMessageAt) {
      return false;
    }

    const elapsedSeconds = (timestamp.getTime() - state.lastMessageAt.getTime()) / 1000;
    return elapsedSeconds < this.config.BOT_REPLY_COOLDOWN_SECONDS;
  }
}

function normalize(text: string): string {
  return text.trim().toLowerCase();
}

function firstToken(text: string): string {
  return text.split(/\s+/)[0] ?? "";
}

function isSameUtcDay(left: Date, right: Date): boolean {
  return (
    left.getUTCFullYear() === right.getUTCFullYear() &&
    left.getUTCMonth() === right.getUTCMonth() &&
    left.getUTCDate() === right.getUTCDate()
  );
}

function buildDigest(topic: string): string {
  return [
    `Here is a quick ${topic} digest:`,
    "1. Watch for model launches, pricing changes, and API deprecations.",
    "2. Track product updates from OpenAI, Anthropic, Google, Meta, Microsoft, and startups.",
    "3. Verify claims before sharing; I can be connected to RSS/news APIs next."
  ].join("\n");
}
