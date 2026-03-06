// frontend/src/api.ts
import type { ChatResponse, Message } from "./types";

export async function sendMessage(messages: Message[]): Promise<string> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data: ChatResponse = await response.json() as ChatResponse;
  return data.reply;
}
