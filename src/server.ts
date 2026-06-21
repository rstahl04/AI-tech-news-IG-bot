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

app.get("/", (_req, res) => {
  res.type("html").send(renderHomePage());
});

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

function renderHomePage(): string {
  const platforms = [...adapters.keys()].join(", ");

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(config.BOT_NAME)}</title>
    <style>
      body {
        background: #0f172a;
        color: #e2e8f0;
        font-family: Arial, sans-serif;
        line-height: 1.5;
        margin: 0;
        padding: 32px;
      }
      main {
        background: #111827;
        border: 1px solid #334155;
        border-radius: 16px;
        margin: 0 auto;
        max-width: 760px;
        padding: 28px;
      }
      code {
        background: #1e293b;
        border-radius: 6px;
        padding: 2px 6px;
      }
      a {
        color: #38bdf8;
      }
      .ok {
        color: #86efac;
        font-weight: bold;
      }
    </style>
  </head>
  <body>
    <main>
      <p class="ok">Running</p>
      <h1>${escapeHtml(config.BOT_NAME)}</h1>
      <p>This DM bot is ready to receive webhook events for ${escapeHtml(platforms)}.</p>
      <h2>User commands</h2>
      <ul>
        <li><code>SUBSCRIBE</code> - opt in</li>
        <li><code>LATEST</code> - get the latest digest</li>
        <li><code>HELP</code> - see commands</li>
        <li><code>STOP</code> - unsubscribe</li>
      </ul>
      <h2>Useful links</h2>
      <ul>
        <li><a href="/health">Health check JSON</a></li>
        <li><code>/webhooks/instagram</code></li>
        <li><code>/webhooks/tiktok</code></li>
        <li><code>/webhooks/twitter</code></li>
      </ul>
      <p>Next step: add official platform credentials in <code>.env</code>, then configure these webhook URLs in each platform dashboard.</p>
    </main>
  </body>
</html>`;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

if (process.env.NODE_ENV !== "test") {
  app.listen(config.PORT, config.HOST, () => {
    logger.info({ host: config.HOST, port: config.PORT }, "DM bot listening");
  });
}

export { app };
