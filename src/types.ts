export type Platform = "instagram" | "tiktok" | "twitter";

export interface IncomingMessage {
  id: string;
  platform: Platform;
  senderId: string;
  recipientId?: string;
  text: string;
  timestamp: Date;
  raw: unknown;
}

export interface OutgoingMessage {
  platform: Platform;
  recipientId: string;
  text: string;
}

export interface BotContext {
  lastInbound: IncomingMessage;
}

export interface BotDecision {
  reply?: string;
  reason: string;
}

export interface PlatformAdapter {
  readonly platform: Platform;
  parseWebhook(payload: unknown): IncomingMessage[];
  sendMessage(message: OutgoingMessage): Promise<void>;
}

export interface WebhookVerification {
  challenge: string;
  isValid: boolean;
}
