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
    let fiber = canvas[fiberKey];
    for (let i = 0; i < 60 && fiber; i++) {
      if (fiber.dependencies && fiber.dependencies.firstContext) {
        let ctx = fiber.dependencies.firstContext;
        while (ctx) {
          if (
            ctx.context &&
            ctx.context._currentValue &&
            ctx.context._currentValue.viewer
          ) {
            window.__chatvrm_viewer = ctx.context._currentValue.viewer;
            return window.__chatvrm_viewer;
          }
          ctx = ctx.next;
        }
      }
      fiber = fiber.return;
    }
    return null;
  }

  function connectToControlServer() {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log("[bridge] Connected to avatar control server");
      ws.send(JSON.stringify({ type: "identify", role: "renderer" }));
    };

    ws.onmessage = async (event) => {
      try {
        const msg = JSON.parse(event.data);

        if (msg.type === "startSpeaking") {
          const viewer = findViewer();
          if (!viewer || !viewer.model) {
            console.warn("[bridge] Viewer/model not ready, skipping speech");
            return;
          }

          const audioUrl = HTTP_URL + msg.audioUrl;
          console.log(
            "[bridge] Speaking:",
            msg.text?.substring(0, 50),
            "emotion:",
            msg.emotion,
          );

          try {
            // Resume AudioContext if suspended (Chrome blocks until user interaction)
            if (viewer.model._lipSync?.audioContext?.state === "suspended") {
              await viewer.model._lipSync.audioContext.resume();
            }

            const response = await fetch(audioUrl);
            const audioBuffer = await response.arrayBuffer();
            const screenplay = {
              expression: msg.emotion || "neutral",
              talk: {
                message: msg.text,
                speakerX: 0,
                speakerY: 0,
                style: "talk",
              },
            };
            await viewer.model.speak(audioBuffer, screenplay);
            console.log("[bridge] Speech complete");
            ws.send(JSON.stringify({ type: "speechEnd", id: msg.id }));
          } catch (err) {
            console.error("[bridge] Audio fetch/play failed:", err);
          }
        }

        if (msg.type === "updateExpression") {
          const viewer = findViewer();
          if (viewer?.model?.emoteController) {
            viewer.model.emoteController.playEmotion(msg.expression);
          }
        }
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
