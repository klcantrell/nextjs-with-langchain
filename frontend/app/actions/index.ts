"use server";

import { createStreamableValue } from "ai/rsc";

export type Message = {
  role: "user" | "assistant" | "system";
  content: string;
};

export async function continueConversation(messages: Message[]) {
  const formattedMessages = messages.flatMap((message) => {
    switch (message.role) {
      case "system":
        return [
          {
            role: "system",
            content: message.content,
          },
        ];
      case "assistant":
        if (typeof message.content === "string") {
          return [
            {
              role: "ai",
              content: message.content,
            },
          ];
        }
        return [];
      case "user":
        if (typeof message.content === "string") {
          return [
            {
              role: "human",
              content: message.content,
            },
          ];
        }
        return [];
      default:
        return [];
    }
  });

  const response = await fetch("http://backend:8000", {
    // disable Next.js's caching mechanism so that the response is actually streamed
    // without this, the response would arrive in one big chunk in the stream reader code below
    // this behavior seems unique to Next.js. tests in node and bun show that responses are streamed
    // as expected regardless of the cache setting
    cache: "no-cache",
    method: "POST",
    body: JSON.stringify({ messages: formattedMessages }),
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok || !response.body) {
    return createStreamableValue("").value;
  }

  const responseStream = response.body.pipeThrough(
    new TextDecoderStream("utf-8")
  );

  return createStreamableValue(responseStream).value;
}
