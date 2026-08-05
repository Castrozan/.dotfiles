(function registerCubeLatticeScene() {
  const FULL_SURFACE_TRIANGLE_STRIP = new Float32Array([
    -1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0,
  ]);
  const TRIANGLE_STRIP_VERTEX_COUNT = 4;

  function compileShader(gl, shaderType, shaderSource) {
    const shader = gl.createShader(shaderType);
    gl.shaderSource(shader, shaderSource);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error(
        "ambient-canvas cube-lattice shader failed to compile: " +
          gl.getShaderInfoLog(shader),
      );
    }
    return shader;
  }

  function linkCubeLatticeProgram(gl) {
    const shaders = window.AmbientCanvasCubeLatticeShaders;
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
        "ambient-canvas cube-lattice program failed to link: " +
          gl.getProgramInfoLog(program),
      );
    }
    return program;
  }

  function uploadFullSurfaceQuad(gl) {
    const quadBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, quadBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, FULL_SURFACE_TRIANGLE_STRIP, gl.STATIC_DRAW);
    return quadBuffer;
  }

  function createCubeLatticeRenderer(canvasElement, options) {
    const gl = canvasElement.getContext("webgl", {
      antialias: false,
      alpha: false,
      preserveDrawingBuffer:
        (options && options.preserveDrawingBuffer) || false,
    });
    if (!gl) {
      console.error(
        "ambient-canvas: WebGL unavailable for a cube-lattice pane",
      );
      return { render() {}, resize() {}, dispose() {} };
    }

    const program = linkCubeLatticeProgram(gl);
    const quadBuffer = uploadFullSurfaceQuad(gl);
    const clipPositionAttribute = gl.getAttribLocation(
      program,
      "a_clip_position",
    );
    const resolutionUniform = gl.getUniformLocation(program, "u_resolution");
    const timeUniform = gl.getUniformLocation(program, "u_time");

    gl.clearColor(...window.AmbientCanvasPalette.backgroundGlColor, 1.0);
    gl.viewport(0, 0, canvasElement.width, canvasElement.height);

    return {
      render(elapsedSeconds) {
        gl.clear(gl.COLOR_BUFFER_BIT);
        gl.useProgram(program);
        gl.bindBuffer(gl.ARRAY_BUFFER, quadBuffer);
        gl.enableVertexAttribArray(clipPositionAttribute);
        gl.vertexAttribPointer(clipPositionAttribute, 2, gl.FLOAT, false, 0, 0);
        gl.uniform2f(
          resolutionUniform,
          canvasElement.width,
          canvasElement.height,
        );
        gl.uniform1f(timeUniform, elapsedSeconds);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, TRIANGLE_STRIP_VERTEX_COUNT);
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
  window.AMBIENT_CANVAS_SCENE_FACTORIES["cube-lattice"] =
    createCubeLatticeRenderer;
})();
