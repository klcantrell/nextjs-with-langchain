import AiMessage from "@/components/AiMessage";
import { createStreamableValue } from "ai/rsc";

// because Next.js's patch of the fetch API somehow causes streams to all arrive in one big chunk
// axios uses Node's underlying HTTP module rather than the fetch API
import axios from "axios";

export function getAiMessage() {
  const stream = createStreamableValue<string>();
  const decoder = new TextDecoder();

  (async () => {
    const aiResponse = await axios.get("http://backend:8000", {
      responseType: "stream",
    });
    aiResponse.data.on("data", (chunk: Uint8Array) => {
      stream.update(decoder.decode(chunk));
    });

    aiResponse.data.on("end", () => {
      stream.done();
    });
  })();

  return stream.value;
}

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <AiMessage text={getAiMessage()} />
    </main>
  );
}
