# Creator AI Chatbot Starter

This repository is a TypeScript starter API for a creator-business AI chat
assistant. It is designed for teams that want to sell a compliant messaging
assistant to adult creators, including creators who operate OnlyFans accounts,
without building risky account scraping or credential-sharing automation.

The service returns **draft replies** for a creator or creator team to review.
It does not auto-send messages, impersonate a creator in real time, bypass
platform controls, or store platform credentials.

## What it includes

- Express API with `POST /api/chat/suggest`
- Creator persona configuration for tone, offers, boundaries, and disclosure
- Age-verification and AI-consent gates
- Safety routing for underage, non-consensual, doxxing, explicit custom,
  billing, refund, and off-platform requests
- OpenAI integration when `OPENAI_API_KEY` is configured
- Deterministic local fallback when no API key is present
- Unit tests for safety and chat orchestration

## Why the product is scoped this way

OnlyFans and similar platforms may restrict unofficial automation, scraping,
credential sharing, or off-platform payment steering. Build this as a
creator-operated assistant first:

1. The creator or their team exports/enters recent conversation context.
2. The API suggests a safe draft reply.
3. A human reviews, edits, and sends the final message inside the platform.

If you later add a direct platform integration, use approved APIs, explicit
creator authorization, visible AI disclosure where required, audit logs, and a
human-review queue for sensitive conversations.

## Quick start

```bash
npm install
cp .env.example .env
npm run dev
```

The server starts on `http://localhost:3000` by default.

Run checks:

```bash
npm test
npm run typecheck
npm run build
```

## Example request

```bash
curl -X POST http://localhost:3000/api/chat/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "creatorId": "creator_123",
    "fan": {
      "platformUserId": "fan_456",
      "displayName": "Sam",
      "isAgeVerified": true,
      "consentedToAiAssistant": true
    },
    "conversation": [
      {
        "role": "fan",
        "content": "Loved your latest post. What are you sharing this week?"
      }
    ],
    "persona": {
      "displayName": "Maya",
      "tone": "playful",
      "offers": [
        "Mention that the creator has a new post dropping today.",
        "Invite the fan to check pinned offers for current bundles."
      ],
      "disclosure": "AI-assisted draft. Human review required before sending."
    }
  }'
```

Example response:

```json
{
  "requestId": "abc123",
  "status": "suggested",
  "disclosure": "AI-assisted draft. Human review required before sending.",
  "reply": "Thanks for the message, Sam. I can help draft a reply, but the creator should review this before it is sent. For custom content, pricing, or sensitive requests, the creator will follow up directly.",
  "safety": {
    "decision": "allow",
    "reasons": ["Conversation passed baseline safety checks."],
    "matchedRules": []
  },
  "shouldSendAutomatically": false
}
```

## API behavior

### `POST /api/chat/suggest`

Returns one of three statuses:

- `suggested`: low-risk conversation; returns an AI-assisted draft.
- `needs_human_review`: sensitive but not blocked; returns a handoff message.
- `blocked`: unsafe or non-compliant; no reply is generated.

The response always includes `shouldSendAutomatically: false` so downstream
clients do not accidentally auto-post drafts.

### Required fan fields

- `platformUserId`: stable platform-side fan identifier.
- `isAgeVerified`: must be `true`.
- `consentedToAiAssistant`: must be `true`, or your workflow must show clear
  AI-assistance disclosure before use.

## Commercialization roadmap

To turn this into a sellable SaaS product for creators, add:

1. Creator dashboard for personas, boundaries, canned offers, and review queue.
2. Team accounts with roles for creators, chatters, and managers.
3. Audit trail for generated drafts, reviewer edits, and final approvals.
4. CRM-style fan notes that avoid sensitive personal data.
5. Billing with plan limits for seats, creators, and monthly draft volume.
6. Analytics for response time, review rate, conversion, and blocked messages.
7. Approved platform integrations or browser-extension workflows that keep
   the creator in control and comply with platform terms.

## Environment variables

See `.env.example`.

- `OPENAI_API_KEY`: optional key for model-backed drafts.
- `OPENAI_MODEL`: defaults to `gpt-4.1-mini`.
- `PORT`: defaults to `3000`.
- `CORS_ORIGIN`: comma-separated allowed origins.

## Safety notes

This starter is intentionally conservative. It blocks or escalates messages
that mention minors, coercion, doxxing, explicit custom content, billing,
refunds, tips, and off-platform transactions. Treat these checks as a baseline,
not a complete legal or trust-and-safety program.
