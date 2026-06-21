import { createHmac } from "node:crypto";
import type { AppConfig } from "../config.js";
import type { IncomingMessage, OutgoingMessage, PlatformAdapter, WebhookVerification } from "../types.js";

interface TwitterWebhookPayload {
  direct_message_events?: Array<{
    id?: string;
    created_timestamp?: string;
    message_create?: {
      sender_id?: string;
      target?: {
        recipient_id?: string;
      };
      message_data?: {
        text?: string;
      };
    };
  }>;
}

export class TwitterAdapter implements PlatformAdapter {
  readonly platform = "twitter" as const;

  constructor(private readonly config: AppConfig) {}

  verifyCrc(query: Record<string, unknown>): WebhookVerification {
    const crcToken = query.crc_token;

    if (!this.config.TWITTER_CONSUMER_SECRET || typeof crcToken !== "string") {
      return {
        challenge: "",
        isValid: false
      };
    }

    const hmac = createHmac("sha256", this.config.TWITTER_CONSUMER_SECRET)
      .update(crcToken)
      .digest("base64");

    return {
      challenge: JSON.stringify({ response_token: `sha256=${hmac}` }),
      isValid: true
    };
  }

  parseWebhook(payload: unknown): IncomingMessage[] {
    const body = payload as TwitterWebhookPayload;

    return (body.direct_message_events ?? [])
      .map((event): IncomingMessage | undefined => {
        const messageCreate = event.message_create;
        const senderId = messageCreate?.sender_id;
        const text = messageCreate?.message_data?.text;

        if (!senderId || !text) {
          return undefined;
        }

        return {
          id: event.id ?? `${senderId}:${event.created_timestamp ?? Date.now()}`,
          platform: this.platform,
          senderId,
          recipientId: messageCreate.target?.recipient_id,
          text,
          timestamp: new Date(Number(event.created_timestamp ?? Date.now())),
          raw: event
        };
      })
      .filter((message): message is IncomingMessage => Boolean(message));
  }

  async sendMessage(message: OutgoingMessage): Promise<void> {
    if (!this.config.TWITTER_BEARER_TOKEN) {
      throw new Error("TWITTER_BEARER_TOKEN is required to send Twitter/X DMs.");
    }

    const response = await fetch(
      `${this.config.TWITTER_API_BASE_URL}/2/dm_conversations/with/${message.recipientId}/messages`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.config.TWITTER_BEARER_TOKEN}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          text: message.text
        })
      }
    );

    if (!response.ok) {
      throw new Error(`Twitter/X send failed: ${response.status} ${await response.text()}`);
    }
  }
}
