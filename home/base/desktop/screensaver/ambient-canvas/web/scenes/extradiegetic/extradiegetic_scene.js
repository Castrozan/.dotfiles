(function registerExtradiegeticScene() {
  const EXTRADIEGETIC_POINT_COUNT = 340000;
  const DITHER_DOT_PIXELS_AT_1080P = 2.3;
  const REFERENCE_FRAME_HEIGHT_PIXELS = 1080;
  const SPHERE_RADIUS_MEDIAN = 0.208;
  const SPHERE_RADIUS_SWING = 0.014;
  const SPHERE_RADIUS_RADIANS_PER_SECOND = 0.21;
  const PUPIL_RADIUS_MEDIAN = 0.176;
  const PUPIL_RADIUS_SWING = 0.021;
  const PUPIL_RADIUS_RADIANS_PER_SECOND = 0.13;

  function compileShader(gl, shaderType, shaderSource) {
    const shader = gl.createShader(shaderType);
    gl.shaderSource(shader, shaderSource);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error(
        "ambient-canvas extradiegetic shader failed to compile: " +
          gl.getShaderInfoLog(shader),
      );
    }
    return shader;
  }

  function linkExtradiegeticProgram(gl) {
    const shaders = window.AmbientCanvasExtradiegeticShaders;
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
        "ambient-canvas extradiegetic program failed to link: " +
          gl.getProgramInfoLog(program),
      );
    }
    return program;
  }

  function uploadPointIndices(gl) {
    const pointIndices = new Float32Array(EXTRADIEGETIC_POINT_COUNT);
    for (
      let position = 0;
      position < EXTRADIEGETIC_POINT_COUNT;
      position += 1
    ) {
      pointIndices[position] = position + 1;
    }
    const pointIndexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, pointIndexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, pointIndices, gl.STATIC_DRAW);
    return pointIndexBuffer;
  }

  function createExtradiegeticRenderer(canvasElement, options) {
    const gl = canvasElement.getContext("webgl", {
      antialias: false,
      alpha: false,
      preserveDrawingBuffer:
        (options && options.preserveDrawingBuffer) || false,
    });
    if (!gl) {
      console.error(
        "ambient-canvas: WebGL unavailable for an extradiegetic pane",
      );
      return { render() {}, resize() {}, dispose() {} };
    }

    const program = linkExtradiegeticProgram(gl);
    const pointIndexBuffer = uploadPointIndices(gl);
    const pointIndexAttribute = gl.getAttribLocation(program, "a_point_index");
    const timeUniform = gl.getUniformLocation(program, "u_time");
    const aspectUniform = gl.getUniformLocation(program, "u_aspect");
    const sphereRadiusUniform = gl.getUniformLocation(
      program,
      "u_sphere_radius",
    );
    const pupilRadiusUniform = gl.getUniformLocation(program, "u_pupil_radius");
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
          sphereRadiusUniform,
          SPHERE_RADIUS_MEDIAN +
            SPHERE_RADIUS_SWING *
              Math.sin(elapsedSeconds * SPHERE_RADIUS_RADIANS_PER_SECOND),
        );
        gl.uniform1f(
          pupilRadiusUniform,
          PUPIL_RADIUS_MEDIAN +
            PUPIL_RADIUS_SWING *
              Math.sin(elapsedSeconds * PUPIL_RADIUS_RADIANS_PER_SECOND + 2.3),
        );
        gl.uniform1f(
          pointSizeUniform,
          Math.max(
            1.0,
            (height / REFERENCE_FRAME_HEIGHT_PIXELS) *
              DITHER_DOT_PIXELS_AT_1080P,
          ),
        );
        gl.drawArrays(gl.POINTS, 0, EXTRADIEGETIC_POINT_COUNT);
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
  window.AMBIENT_CANVAS_SCENE_FACTORIES["extradiegetic"] =
    createExtradiegeticRenderer;
})();
