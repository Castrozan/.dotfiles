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

  sendAndAwaitResult(method, params = {}) {
    return new Promise((resolve) => {
      const messageId = this.send(method, params);
      const unsubscribe = this.messageSocketClient.onMessage((rawMessage) => {
        try {
          const message = JSON.parse(rawMessage);
          if (message.id === messageId) {
            unsubscribe();
            resolve(message.result);
          }
        } catch {}
      });
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
