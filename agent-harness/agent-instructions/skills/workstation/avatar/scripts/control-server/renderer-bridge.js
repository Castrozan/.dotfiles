(() => {
  const WS_URL =
    "ws://localhost:" + (window.__AVATAR_WS_PORT || "@avatarWsPort@");
  const HTTP_URL =
    "http://localhost:" + (window.__AVATAR_HTTP_PORT || "@avatarHttpPort@");

  function findViewer() {
    if (window.__chatvrm_viewer) return window.__chatvrm_viewer;
    const canvas = document.querySelector("canvas");
    if (!canvas) return null;
    const fiberKey = Object.keys(canvas).find((k) =>
      k.startsWith("__reactFiber$"),
    );
    if (!fiberKey) return null;
    return _findViewerInFiber(canvas[fiberKey]);
  }

  function _findViewerInFiber(fiber) {
    for (let depth = 0; depth < 60 && fiber; depth++) {
      const viewer = _findViewerInFiberDependencies(fiber);
      if (viewer) return viewer;
      fiber = fiber.return;
    }
    return null;
  }

  function _findViewerInFiberDependencies(fiber) {
    if (fiber.dependencies && fiber.dependencies.firstContext) {
      return _findViewerInDependencies(fiber.dependencies);
    }
    return null;
  }

  function _findViewerInDependencies(dependencies) {
    let context = dependencies.firstContext;
    while (context) {
      const viewer = _findViewerInContext(context);
      if (viewer) return viewer;
      context = context.next;
    }
    return null;
  }

  function _findViewerInContext(context) {
    if (!context.context) return null;
    if (!context.context._currentValue) return null;
    if (!context.context._currentValue.viewer) return null;
    window.__chatvrm_viewer = context.context._currentValue.viewer;
    return window.__chatvrm_viewer;
  }

  function _handleSpeechMessage(message, ws) {
    const viewer = findViewer();
    if (!viewer || !viewer.model) {
      console.warn("[bridge] Viewer/model not ready, skipping speech");
      return;
    }

    const audioUrl = HTTP_URL + message.audioUrl;
    console.log(
      "[bridge] Speaking:",
      message.text?.substring(0, 50),
      "emotion:",
      message.emotion,
    );

    return _playSpeechOnViewer(viewer, message, audioUrl, ws);
  }

  async function _playSpeechOnViewer(viewer, message, audioUrl, ws) {
    try {
      // Resume AudioContext if suspended (Chrome blocks until user interaction)
      if (viewer.model._lipSync?.audioContext?.state === "suspended") {
        await viewer.model._lipSync.audioContext.resume();
      }

      const response = await fetch(audioUrl);
      const audioBuffer = await response.arrayBuffer();
      const screenplay = {
        expression: message.emotion || "neutral",
        talk: {
          message: message.text,
          speakerX: 0,
          speakerY: 0,
          style: "talk",
        },
      };
      await viewer.model.speak(audioBuffer, screenplay);
      console.log("[bridge] Speech complete");
      ws.send(JSON.stringify({ type: "speechEnd", id: message.id }));
    } catch (err) {
      console.error("[bridge] Audio fetch/play failed:", err);
    }
  }

  function _handleExpressionMessage(message) {
    const model = findViewer()?.model;
    if (model?.emoteController) {
      model.emoteController.playEmotion(message.expression);
    }
  }

  async function _handleControlMessage(message, ws) {
    if (message.type === "startSpeaking") {
      await _handleSpeechMessage(message, ws);
    }
    if (message.type === "updateExpression") {
      _handleExpressionMessage(message);
    }
  }

  function connectToControlServer() {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log("[bridge] Connected to avatar control server");
      ws.send(JSON.stringify({ type: "identify", role: "renderer" }));
    };

    ws.onmessage = async (event) => {
      try {
        await _handleControlMessage(JSON.parse(event.data), ws);
      } catch (err) {
        console.error("[bridge] Message parse error:", err);
      }
    };

    ws.onclose = () => {
      console.log("[bridge] Disconnected, reconnecting in 3s...");
      setTimeout(connectToControlServer, 3000);
    };

    ws.onerror = (err) => {
      console.error("[bridge] WebSocket error:", err);
    };
  }

  function waitForViewerAndConnect() {
    const check = setInterval(() => {
      const viewer = findViewer();
      if (viewer && viewer.isReady && viewer.model) {
        clearInterval(check);
        console.log("[bridge] Viewer ready, connecting to control server...");
        connectToControlServer();
      }
    }, 500);
  }

  waitForViewerAndConnect();
})();
