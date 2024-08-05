const decoder = new TextDecoder();

const response = await fetch("http://localhost:8000");

if (response.ok && response.body) {
  const reader = response.body.getReader();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      console.log("chunk", decoder.decode(value));
    }
  } finally {
    reader.releaseLock();
  }
}
