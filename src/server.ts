import cors from "cors";
import express, { type ErrorRequestHandler } from "express";
import helmet from "helmet";
import { pinoHttp } from "pino-http";
import { ZodError } from "zod";

import { allowedOrigins, config } from "./config.js";
import { createChatSuggestion } from "./chatService.js";
import { chatSuggestionRequestSchema } from "./validation.js";

export function buildApp() {
  const app = express();

  app.use(helmet());
  app.use(
    cors({
      origin(origin, callback) {
        if (!origin || allowedOrigins.includes(origin)) {
          callback(null, true);
          return;
        }
        callback(new Error("Origin is not allowed by CORS"));
      }
    })
  );
  app.use(express.json({ limit: "256kb" }));
  app.use(pinoHttp());

  app.get("/health", (_req, res) => {
    res.json({ ok: true });
  });

  app.post("/api/chat/suggest", async (req, res, next) => {
    try {
      const payload = chatSuggestionRequestSchema.parse(req.body);
      const suggestion = await createChatSuggestion(payload);
      const statusCode = suggestion.status === "blocked" ? 422 : 200;

      res.status(statusCode).json(suggestion);
    } catch (error) {
      next(error);
    }
  });

  const errorHandler: ErrorRequestHandler = (error, _req, res, _next) => {
    if (error instanceof ZodError) {
      res.status(400).json({
        error: "invalid_request",
        details: error.issues.map((issue) => ({
          path: issue.path.join("."),
          message: issue.message
        }))
      });
      return;
    }

    res.status(500).json({
      error: "internal_server_error",
      message:
        config.NODE_ENV === "production"
          ? "Something went wrong."
          : error instanceof Error
            ? error.message
            : "Unknown error"
    });
  };

  app.use(errorHandler);

  return app;
}

if (process.env.NODE_ENV !== "test") {
  const app = buildApp();
  app.listen(config.PORT, () => {
    console.log(`Creator AI chatbot API listening on port ${config.PORT}`);
  });
}
