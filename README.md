# AI Tech News DM Bot

A TypeScript webhook service for a compliant direct-message bot that can be connected to:

- Instagram via Meta's Messenger API for Instagram
- Twitter/X via direct-message webhooks and send APIs
- TikTok through an approved TikTok Business Messaging provider or approved internal integration

The bot intentionally avoids browser automation, credential sharing, scraping, or unsolicited bulk messaging. It only replies to inbound DMs and includes opt-in, unsubscribe, cooldown, and daily-limit controls.

## Features

- Shared DM bot engine for all platforms
- `SUBSCRIBE`, `LATEST`, `HELP`, and `STOP` commands
- Per-user opt-in state
- Reply cooldown and daily message caps
- Instagram webhook verification and app-secret signature checks
- Twitter/X CRC verification support
- TikTok provider-compatible webhook/signature flow
- Unit tests for the safety policy layer

## Quick start

```bash
npm install
cp .env.example .env
npm run dev
```

The default server runs on port `3000`.

Health check:

```bash
curl http://localhost:3000/health
```

## Webhook URLs

Configure these URLs in the relevant platform developer dashboard or approved messaging provider:

- Instagram GET/POST: `https://your-domain.example/webhooks/instagram`
- TikTok POST: `https://your-domain.example/webhooks/tiktok`
- Twitter/X GET/POST: `https://your-domain.example/webhooks/twitter`

For local testing, expose your server with a tunnel such as ngrok or Cloudflare Tunnel and set `PUBLIC_BASE_URL` to that public URL.

## Environment variables

Copy `.env.example` to `.env` and fill in credentials:

| Variable | Purpose |
| --- | --- |
| `BOT_NAME` | Display name used in replies |
| `BOT_TOPIC` | Topic used in replies, e.g. `AI technology news` |
| `BOT_DAILY_MESSAGE_LIMIT` | Max replies per user per UTC day |
| `BOT_REPLY_COOLDOWN_SECONDS` | Minimum seconds between replies per user |
| `INSTAGRAM_VERIFY_TOKEN` | Meta webhook verification token you choose |
| `INSTAGRAM_PAGE_ACCESS_TOKEN` | Meta page/account token for sending Instagram DMs |
| `INSTAGRAM_APP_SECRET` | Meta app secret for `x-hub-signature-256` checks |
| `TIKTOK_WEBHOOK_SECRET` | Secret from your approved TikTok messaging provider |
| `TIKTOK_API_BASE_URL` | Base URL for your approved TikTok messaging provider |
| `TIKTOK_ACCESS_TOKEN` | Token for that TikTok messaging provider |
| `TWITTER_BEARER_TOKEN` | Token with DM send permissions for X |
| `TWITTER_CONSUMER_SECRET` | X consumer secret for CRC challenge responses |

## Commands users can send

- `SUBSCRIBE` - opt in to bot replies
- `LATEST` - receive the current digest
- `HELP` - show available commands
- `STOP` - unsubscribe

## Development

```bash
npm run typecheck
npm test
npm run build
npm start
```

## Next steps

This foundation uses a simple static digest. To turn it into a richer AI tech news bot, add a service that fetches trusted sources (RSS feeds, newsletters, or APIs), summarizes them, and returns those summaries from `src/bot.ts`. Keep the opt-in, unsubscribe, cooldown, and rate-limit checks in place when adding scheduled or AI-generated content.
