import type { Platform } from "./types.js";

export interface UserConversationState {
  dailyMessageCount: number;
  lastMessageAt?: Date;
  optedIn: boolean;
  stopped: boolean;
  updatedAt: Date;
}

export interface ConversationStore {
  get(platform: Platform, senderId: string): UserConversationState | undefined;
  save(platform: Platform, senderId: string, state: UserConversationState): void;
}

export class InMemoryConversationStore implements ConversationStore {
  private readonly states = new Map<string, UserConversationState>();

  get(platform: Platform, senderId: string): UserConversationState | undefined {
    return this.states.get(this.key(platform, senderId));
  }

  save(platform: Platform, senderId: string, state: UserConversationState): void {
    this.states.set(this.key(platform, senderId), state);
  }

  private key(platform: Platform, senderId: string): string {
    return `${platform}:${senderId}`;
  }
}
