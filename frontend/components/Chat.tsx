"use client";

import { StreamableValue, useStreamableValue } from "ai/rsc";
import { useEffect, useState } from "react";

type AiMessageProps = {
  text: StreamableValue<string>;
};
export default function Chat({ text }: AiMessageProps) {
  const [messageStream] = useStreamableValue(text);

  useEffect(() => {
    if (messageStream != null) {
      setMessage((previous) => previous + messageStream);
    }
  }, [messageStream]);

  const [message, setMessage] = useState("");

  return (
    <p className="text-xl border-blue-500 border-[1px] min-h-[100px] min-w-full p-8 rounded">
      {message}
    </p>
  );
}
