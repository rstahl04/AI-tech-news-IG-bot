import express, { type Request, type Response } from "express";
import { pinoHttp } from "pino-http";
import { DmBot } from "./bot.js";
import { config } from "./config.js";
import { logger } from "./logger.js";
import { InstagramAdapter } from "./platforms/instagram.js";
import { TikTokAdapter } from "./platforms/tiktok.js";
import { TwitterAdapter } from "./platforms/twitter.js";
import { InMemoryConversationStore } from "./state.js";
import type { IncomingMessage, Platform, PlatformAdapter } from "./types.js";

declare module "http" {
  interface IncomingMessage {
    rawBody?: Buffer;
  }
}

const app = express();
const store = new InMemoryConversationStore();
const bot = new DmBot(store, config);
const instagram = new InstagramAdapter(config);
const tiktok = new TikTokAdapter(config);
const twitter = new TwitterAdapter(config);

const adapters = new Map<Platform, PlatformAdapter>([
  [instagram.platform, instagram],
  [tiktok.platform, tiktok],
  [twitter.platform, twitter]
]);

app.use(
  express.json({
    verify: (req, _res, buffer) => {
      req.rawBody = Buffer.from(buffer);
    }
  })
);
app.use(pinoHttp({ logger }));

app.get("/health", (_req, res) => {
  res.json({
    ok: true,
    bot: config.BOT_NAME,
    platforms: [...adapters.keys()]
  });
});

app.get("/webhooks/instagram", (req, res) => {
  const verification = instagram.verifyWebhook(req.query);
  if (!verification.isValid) {
    res.sendStatus(403);
    return;
  }

  res.status(200).send(verification.challenge);
});

app.post("/webhooks/instagram", async (req, res) => {
  if (!instagram.verifySignature(req.rawBody ?? Buffer.alloc(0), req.header("x-hub-signature-256"))) {
    res.sendStatus(401);
    return;
  }

  await handleWebhook(instagram, req, res);
});

app.post("/webhooks/tiktok", async (req, res) => {
  if (!tiktok.verifySignature(req.rawBody ?? Buffer.alloc(0), req.header("x-tiktok-signature"))) {
    res.sendStatus(401);
    return;
  }

  await handleWebhook(tiktok, req, res);
});

app.get("/webhooks/twitter", (req, res) => {
  const verification = twitter.verifyCrc(req.query);
  if (!verification.isValid) {
    res.sendStatus(403);
    return;
  }

  res.type("application/json").status(200).send(verification.challenge);
});

app.post("/webhooks/twitter", async (req, res) => {
  await handleWebhook(twitter, req, res);
});

app.use((_req, res) => {
  res.status(404).json({ error: "not_found" });
});

async function handleWebhook(adapter: PlatformAdapter, req: Request, res: Response): Promise<void> {
  const messages = adapter.parseWebhook(req.body);
  const results = [];

  for (const message of messages) {
    const result = await handleIncoming(adapter, message);
    results.push(result);
  }

  res.status(200).json({
    received: messages.length,
    results
  });
}

async function handleIncoming(adapter: PlatformAdapter, message: IncomingMessage): Promise<{
  messageId: string;
  reason: string;
  replied: boolean;
}> {
  const decision = bot.decide(message);

  if (!decision.reply) {
    logger.info(
      {
        platform: message.platform,
        messageId: message.id,
        reason: decision.reason
      },
      "Skipping DM reply"
    );

    return {
      messageId: message.id,
      reason: decision.reason,
      replied: false
    };
  }

  await adapter.sendMessage({
    platform: message.platform,
    recipientId: message.senderId,
    text: decision.reply
  });

  return {
    messageId: message.id,
    reason: decision.reason,
    replied: true
  };
}

if (process.env.NODE_ENV !== "test") {
  app.listen(config.PORT, config.HOST, () => {
    logger.info({ host: config.HOST, port: config.PORT }, "DM bot listening");
  });
}

export { app };
