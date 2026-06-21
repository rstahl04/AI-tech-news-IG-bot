import { createHmac, timingSafeEqual } from "node:crypto";
import type { AppConfig } from "../config.js";
import type { IncomingMessage, OutgoingMessage, PlatformAdapter } from "../types.js";

interface TikTokProviderPayload {
  events?: Array<{
    id?: string;
    type?: string;
    sender_id?: string;
    recipient_id?: string;
    created_at?: string | number;
    message?: {
      text?: string;
    };
  }>;
}

export class TikTokAdapter implements PlatformAdapter {
  readonly platform = "tiktok" as const;

  constructor(private readonly config: AppConfig) {}

  verifySignature(rawBody: Buffer, signatureHeader: string | undefined): boolean {
    if (!this.config.TIKTOK_WEBHOOK_SECRET) {
      return true;
    }

    if (!signatureHeader) {
      return false;
    }

    const expected = createHmac("sha256", this.config.TIKTOK_WEBHOOK_SECRET)
      .update(rawBody)
      .digest("hex");

    return safeEqual(expected, signatureHeader.replace(/^sha256=/, ""));
  }

  parseWebhook(payload: unknown): IncomingMessage[] {
    const body = payload as TikTokProviderPayload;

    return (body.events ?? [])
      .filter((event) => event.type === undefined || event.type === "message")
      .map((event): IncomingMessage | undefined => {
        const senderId = event.sender_id;
        const text = event.message?.text;

        if (!senderId || !text) {
          return undefined;
        }

        return {
          id: event.id ?? `${senderId}:${event.created_at ?? Date.now()}`,
          platform: this.platform,
          senderId,
          recipientId: event.recipient_id,
          text,
          timestamp: parseProviderTimestamp(event.created_at),
          raw: event
        };
      })
      .filter((message): message is IncomingMessage => Boolean(message));
  }

  async sendMessage(message: OutgoingMessage): Promise<void> {
    if (!this.config.TIKTOK_API_BASE_URL || !this.config.TIKTOK_ACCESS_TOKEN) {
      throw new Error(
        "TikTok DM sending requires TIKTOK_API_BASE_URL and TIKTOK_ACCESS_TOKEN from an approved TikTok messaging provider."
      );
    }

    const response = await fetch(`${this.config.TIKTOK_API_BASE_URL}/dm/messages`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.config.TIKTOK_ACCESS_TOKEN}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        recipient_id: message.recipientId,
        text: message.text
      })
    });

    if (!response.ok) {
      throw new Error(`TikTok provider send failed: ${response.status} ${await response.text()}`);
    }
  }
}

function parseProviderTimestamp(value: string | number | undefined): Date {
  if (typeof value === "number") {
    return new Date(value);
  }

  if (typeof value === "string") {
    const numeric = Number(value);
    return Number.isNaN(numeric) ? new Date(value) : new Date(numeric);
  }

  return new Date();
}

function safeEqual(expectedHex: string, actualHex: string): boolean {
  const expected = Buffer.from(expectedHex, "hex");
  const actual = Buffer.from(actualHex, "hex");

  if (expected.length !== actual.length) {
    return false;
  }

  return timingSafeEqual(expected, actual);
}
