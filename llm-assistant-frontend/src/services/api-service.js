async sendMessage(chatId, messages, temperature = 0.7, maxTokens = 800) {
  const url = new URL(`${this.baseUrl}/chat/stream`);
  url.searchParams.append('chat_id', chatId);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages,
      temperature,
      max_tokens: maxTokens
    })
  });
  return response.body.getReader();
} 