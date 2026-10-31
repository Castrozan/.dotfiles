class ChromeDevtoolsSession {
  constructor(messageSocketClient) {
    this.messageSocketClient = messageSocketClient;
    this.lastMessageId = 0;
  }

  send(method, params = {}) {
    const messageId = ++this.lastMessageId;
    this.messageSocketClient.sendJson({ id: messageId, method, params });
    return messageId;
  }

  sendAndAwaitResult(method, params = {}, timeoutMilliseconds = 10000) {
    return new Promise((resolve, reject) => {
      const messageId = ++this.lastMessageId;
      const timer = setTimeout(() => {
        unsubscribe();
        reject(new Error(`Chrome did not answer ${method}`));
      }, timeoutMilliseconds);
      const unsubscribe = this.messageSocketClient.onMessage((rawMessage) => {
        const message = JSON.parse(rawMessage);
        if (message.id !== messageId) return;
        unsubscribe();
        clearTimeout(timer);
        if (message.error) reject(new Error(message.error.message));
        else resolve(message.result);
      });
      this.messageSocketClient.sendJson({ id: messageId, method, params });
    });
  }

  onEvent(handleEvent) {
    return this.messageSocketClient.onMessage((rawMessage) => {
      try {
        handleEvent(JSON.parse(rawMessage));
      } catch {}
    });
  }

  onOpen(handleOpen) {
    this.messageSocketClient.onOpen(handleOpen);
  }

  onClosed(handleClose) {
    this.messageSocketClient.onClosed(handleClose);
  }

  onError(handleError) {
    this.messageSocketClient.onError(handleError);
  }

  close() {
    this.messageSocketClient.close();
  }
}

module.exports = { ChromeDevtoolsSession };
