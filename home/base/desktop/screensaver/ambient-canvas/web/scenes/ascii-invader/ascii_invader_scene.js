(function registerAsciiInvaderScene() {
  const GLYPH_FIELD_MAXIMUM_SIDE = 1080;

  function compileShader(gl, shaderType, shaderSource) {
    const shader = gl.createShader(shaderType);
    gl.shaderSource(shader, shaderSource);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error(
        "ambient-canvas ascii-invader shader failed to compile: " +
          gl.getShaderInfoLog(shader),
      );
    }
    return shader;
  }

  function linkAsciiInvaderProgram(gl) {
    const shaders = window.AmbientCanvasAsciiInvaderCrtShaders;
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
        "ambient-canvas ascii-invader program failed to link: " +
          gl.getProgramInfoLog(program),
      );
    }
    return program;
  }

  function uploadScreenQuad(gl) {
    const corners = new Float32Array([
      -1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1,
    ]);
    const cornerBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, cornerBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, corners, gl.STATIC_DRAW);
    return cornerBuffer;
  }

  function createGlyphFieldTexture(gl) {
    const texture = gl.createTexture();
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    return texture;
  }

  function createAsciiInvaderRenderer(canvasElement, options) {
    const gl = canvasElement.getContext("webgl", {
      antialias: false,
      alpha: false,
      preserveDrawingBuffer:
        (options && options.preserveDrawingBuffer) || false,
    });
    if (!gl) {
      console.error(
        "ambient-canvas: WebGL unavailable for an ascii-invader pane",
      );
      return { render() {}, resize() {}, dispose() {} };
    }

    const glyphFieldCanvas = document.createElement("canvas");
    const glyphFieldContext = glyphFieldCanvas.getContext("2d");
    const shellPoints =
      window.AmbientCanvasAsciiInvaderShell.buildShellPoints();
    const program = linkAsciiInvaderProgram(gl);
    const cornerBuffer = uploadScreenQuad(gl);
    const glyphFieldTexture = createGlyphFieldTexture(gl);
    const cornerAttribute = gl.getAttribLocation(program, "a_screen_corner");
    const glyphFieldUniform = gl.getUniformLocation(program, "u_glyph_field");
    const timeUniform = gl.getUniformLocation(program, "u_time");
    const resolutionUniform = gl.getUniformLocation(program, "u_resolution");
    const paneAspectUniform = gl.getUniformLocation(program, "u_pane_aspect");

    function resizeGlyphField(pixelWidthDevice, pixelHeightDevice) {
      const side = Math.max(
        320,
        Math.min(
          GLYPH_FIELD_MAXIMUM_SIDE,
          Math.min(pixelWidthDevice, pixelHeightDevice),
        ),
      );
      if (glyphFieldCanvas.width !== side) {
        glyphFieldCanvas.width = side;
        glyphFieldCanvas.height = side;
      }
    }

    resizeGlyphField(canvasElement.width, canvasElement.height);
    gl.clearColor(0.0, 0.0, 0.0, 1.0);
    gl.viewport(0, 0, canvasElement.width, canvasElement.height);

    return {
      render(elapsedSeconds) {
        const width = canvasElement.width;
        const height = canvasElement.height;
        resizeGlyphField(width, height);
        window.AmbientCanvasAsciiInvaderGlyphField.paintGlyphField(
          glyphFieldContext,
          glyphFieldCanvas.width,
          glyphFieldCanvas.height,
          elapsedSeconds,
          shellPoints,
        );

        gl.clear(gl.COLOR_BUFFER_BIT);
        gl.useProgram(program);
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, glyphFieldTexture);
        gl.texImage2D(
          gl.TEXTURE_2D,
          0,
          gl.RGBA,
          gl.RGBA,
          gl.UNSIGNED_BYTE,
          glyphFieldCanvas,
        );
        gl.uniform1i(glyphFieldUniform, 0);
        gl.uniform1f(timeUniform, elapsedSeconds);
        gl.uniform2f(resolutionUniform, width, height);
        gl.uniform1f(paneAspectUniform, width / height);
        gl.bindBuffer(gl.ARRAY_BUFFER, cornerBuffer);
        gl.enableVertexAttribArray(cornerAttribute);
        gl.vertexAttribPointer(cornerAttribute, 2, gl.FLOAT, false, 0, 0);
        gl.drawArrays(gl.TRIANGLES, 0, 6);
      },
      resize(pixelWidthDevice, pixelHeightDevice) {
        gl.viewport(0, 0, pixelWidthDevice, pixelHeightDevice);
        resizeGlyphField(pixelWidthDevice, pixelHeightDevice);
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
  window.AMBIENT_CANVAS_SCENE_FACTORIES["ascii-invader"] =
    createAsciiInvaderRenderer;
})();
