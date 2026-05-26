import { nanoid } from "nanoid";

import { draftReply } from "./aiClient.js";
import { mergePersona } from "./persona.js";
import { evaluateSafety } from "./safety.js";
import type {
  ChatSuggestionRequest,
  ChatSuggestionResponse
} from "./types.js";

export async function createChatSuggestion(
  request: ChatSuggestionRequest
): Promise<ChatSuggestionResponse> {
  const requestId = nanoid();
  const persona = mergePersona(request.persona);
  const safety = evaluateSafety(request.fan, request.conversation);

  if (safety.decision === "block") {
    return {
      requestId,
      status: "blocked",
      disclosure: persona.disclosure,
      safety,
      shouldSendAutomatically: false
    };
  }

  if (safety.decision === "needs_human_review") {
    return {
      requestId,
      status: "needs_human_review",
      disclosure: persona.disclosure,
      reply:
        "Thanks for asking. This needs the creator to review personally, so a human will follow up before anything is confirmed.",
      safety,
      shouldSendAutomatically: false
    };
  }

  const reply = await draftReply({
    persona,
    fanDisplayName: request.fan.displayName,
    conversation: request.conversation
  });

  return {
    requestId,
    status: "suggested",
    disclosure: persona.disclosure,
    reply,
    safety,
    shouldSendAutomatically: false
  };
}
