"use client";

import { readStreamableValue } from "ai/rsc";
import { useState } from "react";

import { Message, graphChat } from "@/app/actions";

export default function GraphChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  return (
    <div className="h-full">
      <div className="overflow-y-scroll border border-slate-100 h-full">
        {messages.map((m, i) => (
          <div key={i} className="whitespace-pre-wrap">
            {m.role === "user" ? "User: " : "AI: "}
            {m.content}
          </div>
        ))}
      </div>

      <form
        className="flex flex-col"
        onSubmit={async (e) => {
          e.preventDefault();
          const newMessages: Message[] = [
            ...messages,
            { content: input, role: "user" },
          ];

          setMessages(newMessages);
          setInput("");

          const result = await graphChat(newMessages);

          for await (const content of readStreamableValue(result)) {
            setMessages([
              ...newMessages,
              {
                role: "assistant",
                content: content ?? "",
              },
            ]);
          }
        }}
      >
        <input
          className="fixed bottom-0 w-full self-center max-w-md p-2 mb-8 border border-gray-300 rounded shadow-xl text-black"
          value={input}
          placeholder="Say something..."
          onChange={(e) => setInput(e.target.value)}
        />
      </form>
    </div>
  );
}
