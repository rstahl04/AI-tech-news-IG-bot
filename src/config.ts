import "dotenv/config";
import { z } from "zod";

const envSchema = z.object({
  PORT: z.coerce.number().int().positive().default(3000),
  PUBLIC_BASE_URL: z.string().url().optional(),
  BOT_NAME: z.string().default("AI Tech News Bot"),
  BOT_TOPIC: z.string().default("AI technology news"),
  BOT_DAILY_MESSAGE_LIMIT: z.coerce.number().int().positive().default(5),
  BOT_REPLY_COOLDOWN_SECONDS: z.coerce.number().int().nonnegative().default(30),
  INSTAGRAM_VERIFY_TOKEN: z.string().optional(),
  INSTAGRAM_PAGE_ACCESS_TOKEN: z.string().optional(),
  INSTAGRAM_APP_SECRET: z.string().optional(),
  TIKTOK_WEBHOOK_SECRET: z.string().optional(),
  TIKTOK_API_BASE_URL: z.string().url().optional(),
  TIKTOK_ACCESS_TOKEN: z.string().optional(),
  TWITTER_API_BASE_URL: z.string().url().default("https://api.x.com"),
  TWITTER_BEARER_TOKEN: z.string().optional(),
  TWITTER_CONSUMER_SECRET: z.string().optional()
});

export const config = envSchema.parse(process.env);

export type AppConfig = typeof config;
