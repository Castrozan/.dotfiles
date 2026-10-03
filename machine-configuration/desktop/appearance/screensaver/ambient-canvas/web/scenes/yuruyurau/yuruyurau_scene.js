(function registerYuruyurauScene() {
  const figureExtentByVariant = {
    twin: 150.0,
    solo: 150.0,
    swirl: 150.0,
    petal: 130.0,
  };

  const YURUYURAU_POINT_COUNT = 20000;
  const FIGURE_FILL_RATIO = 0.4;
  const TIME_STEP_PER_SECOND = ((2.0 * Math.PI) / 45.0) * 15.0;

  const setup = window.AmbientCanvasYuruyurauSetup;

  function createYuruyurauRenderer(canvasElement, options) {
    const gl = canvasElement.getContext("webgl", {
      antialias: true,
      alpha: false,
      preserveDrawingBuffer:
        (options && options.preserveDrawingBuffer) || false,
    });
    if (!gl) {
      console.error("ambient-canvas: WebGL unavailable for a yuruyurau pane");
      return { render() {}, resize() {}, dispose() {} };
    }
    const variantNames = Object.keys(figureExtentByVariant);
    const selectedVariant = resolveSelectedVariant(options, variantNames);
    const figureExtent = figureExtentByVariant[selectedVariant];
    const devicePixelRatio = resolveDevicePixelRatio(options);

    const program = setup.createProgram(gl, selectedVariant);
    const pointIndexBuffer = setup.createPointIndexBuffer(
      gl,
      YURUYURAU_POINT_COUNT,
    );

    const pointIndexAttribute = gl.getAttribLocation(program, "a_point_index");
    const timeUniform = gl.getUniformLocation(program, "u_time");
    const clipUniform = gl.getUniformLocation(program, "u_clip");
    const pointSizeUniform = gl.getUniformLocation(program, "u_point_size");

    gl.clearColor(...window.AmbientCanvasPalette.backgroundGlColor, 1.0);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
    gl.viewport(0, 0, canvasElement.width, canvasElement.height);

    return {
      render(elapsedSeconds) {
        const width = canvasElement.width;
        const height = canvasElement.height;
        const minimumDimension = Math.min(width, height);
        const pixelScale =
          (FIGURE_FILL_RATIO * minimumDimension) / figureExtent;
        gl.clear(gl.COLOR_BUFFER_BIT);
        gl.useProgram(program);
        gl.bindBuffer(gl.ARRAY_BUFFER, pointIndexBuffer);
        gl.enableVertexAttribArray(pointIndexAttribute);
        gl.vertexAttribPointer(pointIndexAttribute, 1, gl.FLOAT, false, 0, 0);
        gl.uniform1f(timeUniform, elapsedSeconds * TIME_STEP_PER_SECOND);
        gl.uniform2f(
          clipUniform,
          pixelScale / (width / 2),
          pixelScale / (height / 2),
        );
        gl.uniform1f(pointSizeUniform, Math.max(1.0, 1.6 * devicePixelRatio));
        gl.drawArrays(gl.POINTS, 0, YURUYURAU_POINT_COUNT);
      },
      resize(pixelWidthDevice, pixelHeightDevice) {
        gl.viewport(0, 0, pixelWidthDevice, pixelHeightDevice);
      },
      dispose() {
        const loseContextExtension = gl.getExtension("WEBGL_lose_context");
        if (loseContextExtension) {
          loseContextExtension.loseContext();
        }
      },
    };
  }

  function resolveSelectedVariant(options, variantNames) {
    return (options && options.variant) || variantNames[0];
  }

  function resolveDevicePixelRatio(options) {
    return (options && options.devicePixelRatio) || 1;
  }

  window.AMBIENT_CANVAS_SCENE_FACTORIES =
    window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
  window.AMBIENT_CANVAS_SCENE_FACTORIES["yuruyurau"] = createYuruyurauRenderer;
})();
