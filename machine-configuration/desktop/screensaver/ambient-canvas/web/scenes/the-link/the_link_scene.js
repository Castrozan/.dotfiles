(function registerTheLinkScene() {
  const THE_LINK_POINT_COUNT = 260000;
  const STREAK_PIXELS_AT_1080P = 4.0;
  const REFERENCE_FRAME_HEIGHT_PIXELS = 1080;
  const DOME_RADIUS_MEDIAN = 2.15;
  const DOME_RADIUS_SWING = 0.22;
  const DOME_RADIUS_RADIANS_PER_SECOND = 0.19;
  const WAIST_GAP_MEDIAN = 0.014;
  const WAIST_GAP_SWING = 0.009;
  const WAIST_GAP_RADIANS_PER_SECOND = 0.33;

  function compileShader(gl, shaderType, shaderSource) {
    const shader = gl.createShader(shaderType);
    gl.shaderSource(shader, shaderSource);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error(
        "ambient-canvas the-link shader failed to compile: " +
          gl.getShaderInfoLog(shader),
      );
    }
    return shader;
  }

  function linkTheLinkProgram(gl) {
    const shaders = window.AmbientCanvasTheLinkShaders;
    const program = gl.createProgram();
    gl.attachShader(
      program,
      compileShader(gl, gl.VERTEX_SHADER, shaders.vertexShaderSource),
    );
    gl.attachShader(
      program,
      compileShader(gl, gl.FRAGMENT_SHADER, shaders.fragmentShaderSource),
    );
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error(
        "ambient-canvas the-link program failed to link: " +
          gl.getProgramInfoLog(program),
      );
    }
    return program;
  }

  function uploadPointIndices(gl) {
    const pointIndices = new Float32Array(THE_LINK_POINT_COUNT);
    for (let position = 0; position < THE_LINK_POINT_COUNT; position += 1) {
      pointIndices[position] = position + 1;
    }
    const pointIndexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, pointIndexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, pointIndices, gl.STATIC_DRAW);
    return pointIndexBuffer;
  }

  function createTheLinkRenderer(canvasElement, options) {
    const gl = canvasElement.getContext("webgl", {
      antialias: false,
      alpha: false,
      preserveDrawingBuffer:
        (options && options.preserveDrawingBuffer) || false,
    });
    if (!gl) {
      console.error("ambient-canvas: WebGL unavailable for a the-link pane");
      return { render() {}, resize() {}, dispose() {} };
    }

    const program = linkTheLinkProgram(gl);
    const pointIndexBuffer = uploadPointIndices(gl);
    const pointIndexAttribute = gl.getAttribLocation(program, "a_point_index");
    const timeUniform = gl.getUniformLocation(program, "u_time");
    const aspectUniform = gl.getUniformLocation(program, "u_aspect");
    const domeRadiusUniform = gl.getUniformLocation(program, "u_dome_radius");
    const waistGapUniform = gl.getUniformLocation(program, "u_waist_gap");
    const pointSizeUniform = gl.getUniformLocation(program, "u_point_size");

    gl.clearColor(...window.AmbientCanvasPalette.backgroundGlColor, 1.0);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
    gl.viewport(0, 0, canvasElement.width, canvasElement.height);

    return {
      render(elapsedSeconds) {
        const width = canvasElement.width;
        const height = canvasElement.height;
        gl.clear(gl.COLOR_BUFFER_BIT);
        gl.useProgram(program);
        gl.bindBuffer(gl.ARRAY_BUFFER, pointIndexBuffer);
        gl.enableVertexAttribArray(pointIndexAttribute);
        gl.vertexAttribPointer(pointIndexAttribute, 1, gl.FLOAT, false, 0, 0);
        gl.uniform1f(timeUniform, elapsedSeconds);
        gl.uniform1f(aspectUniform, width / height);
        gl.uniform1f(
          domeRadiusUniform,
          DOME_RADIUS_MEDIAN +
            DOME_RADIUS_SWING *
              Math.sin(elapsedSeconds * DOME_RADIUS_RADIANS_PER_SECOND + 1.1),
        );
        gl.uniform1f(
          waistGapUniform,
          WAIST_GAP_MEDIAN +
            WAIST_GAP_SWING *
              Math.sin(elapsedSeconds * WAIST_GAP_RADIANS_PER_SECOND),
        );
        gl.uniform1f(
          pointSizeUniform,
          Math.max(
            1.0,
            (height / REFERENCE_FRAME_HEIGHT_PIXELS) * STREAK_PIXELS_AT_1080P,
          ),
        );
        gl.drawArrays(gl.POINTS, 0, THE_LINK_POINT_COUNT);
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

  window.AMBIENT_CANVAS_SCENE_FACTORIES =
    window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
  window.AMBIENT_CANVAS_SCENE_FACTORIES["the-link"] = createTheLinkRenderer;
})();
