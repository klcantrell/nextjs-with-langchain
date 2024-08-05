// for testing with Node

const response = await fetch("http://localhost:8000");

if (response.ok && response.body) {
  const reader = response.body
    .pipeThrough(new TextDecoderStream("utf-8"))
    .getReader();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      console.log("chunk", value);
    }
  } finally {
    reader.releaseLock();
  }
}
