import AiMessage from "@/components/AiMessage";
import { createStreamableValue } from "ai/rsc";

export function getAiMessage() {
  const stream = createStreamableValue<string>();

  (async () => {
    const response = await fetch("http://backend:8000", {
      // disable Next.js's caching mechanism so that the response is actually streamed
      // without this, the response would arrive in one big chunk in the stream reader code below 
      // this behavior seems unique to Next.js. tests in node and bun show that responses are streamed
      // as expected regardless of the cache setting
      cache: "no-cache",
    });

    if (!response.ok || !response.body) {
      stream.done();
      return;
    }

    const reader = response.body
      .pipeThrough(new TextDecoderStream("utf-8"))
      .getReader();

    try {
      while (true) {
        const { done, value: chunk } = await reader.read();
        if (done) {
          break;
        }

        stream.update(chunk);
      }
    } finally {
      stream.done();
      reader.releaseLock();
    }
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
