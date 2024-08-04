const decoder = new TextDecoder();

const aiResponse = await fetch("http://localhost:8000");

if (aiResponse.ok && aiResponse.body) {
  const reader = aiResponse.body.getReader();

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
