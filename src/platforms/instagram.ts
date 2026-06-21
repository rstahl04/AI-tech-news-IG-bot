import { createHmac, timingSafeEqual } from "node:crypto";
import type { AppConfig } from "../config.js";
import type { IncomingMessage, OutgoingMessage, PlatformAdapter, WebhookVerification } from "../types.js";

interface InstagramWebhookPayload {
  entry?: Array<{
    messaging?: Array<{
      sender?: { id?: string };
      recipient?: { id?: string };
      timestamp?: number;
      message?: {
        mid?: string;
        text?: string;
      };
    }>;
  }>;
}

export class InstagramAdapter implements PlatformAdapter {
  readonly platform = "instagram" as const;

  constructor(private readonly config: AppConfig) {}

  verifyWebhook(query: Record<string, unknown>): WebhookVerification {
    const mode = query["hub.mode"];
    const token = query["hub.verify_token"];
    const challenge = query["hub.challenge"];

    return {
      challenge: typeof challenge === "string" ? challenge : "",
      isValid:
        mode === "subscribe" &&
        typeof token === "string" &&
        token === this.config.INSTAGRAM_VERIFY_TOKEN &&
        typeof challenge === "string"
    };
  }

  verifySignature(rawBody: Buffer, signatureHeader: string | undefined): boolean {
    if (!this.config.INSTAGRAM_APP_SECRET) {
      return true;
    }

    if (!signatureHeader?.startsWith("sha256=")) {
      return false;
    }

    const expected = createHmac("sha256", this.config.INSTAGRAM_APP_SECRET)
      .update(rawBody)
      .digest("hex");
    const actual = signatureHeader.slice("sha256=".length);

    return safeEqual(expected, actual);
  }

  parseWebhook(payload: unknown): IncomingMessage[] {
    const body = payload as InstagramWebhookPayload;
    const messages: IncomingMessage[] = [];

    for (const entry of body.entry ?? []) {
      for (const event of entry.messaging ?? []) {
        const text = event.message?.text;
        const senderId = event.sender?.id;

        if (!text || !senderId) {
          continue;
        }

        messages.push({
          id: event.message?.mid ?? `${senderId}:${event.timestamp ?? Date.now()}`,
          platform: this.platform,
          senderId,
          recipientId: event.recipient?.id,
          text,
          timestamp: new Date(event.timestamp ?? Date.now()),
          raw: event
        });
      }
    }

    return messages;
  }

  async sendMessage(message: OutgoingMessage): Promise<void> {
    if (!this.config.INSTAGRAM_PAGE_ACCESS_TOKEN) {
      throw new Error("INSTAGRAM_PAGE_ACCESS_TOKEN is required to send Instagram DMs.");
    }

    const url = new URL("https://graph.facebook.com/v20.0/me/messages");
    url.searchParams.set("access_token", this.config.INSTAGRAM_PAGE_ACCESS_TOKEN);

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        recipient: { id: message.recipientId },
        message: { text: message.text },
        messaging_type: "RESPONSE"
      })
    });

    if (!response.ok) {
      throw new Error(`Instagram send failed: ${response.status} ${await response.text()}`);
    }
  }
}

function safeEqual(expectedHex: string, actualHex: string): boolean {
  const expected = Buffer.from(expectedHex, "hex");
  const actual = Buffer.from(actualHex, "hex");

  if (expected.length !== actual.length) {
    return false;
  }

  return timingSafeEqual(expected, actual);
}
