(function registerYuruyurauScene() {
  const sharedFragmentShaderSource = `
    precision mediump float;
    void main() {
      float radiusFromCenter = length(gl_PointCoord - vec2(0.5));
      if (radiusFromCenter > 0.5) {
        discard;
      }
      float glow = 1.0 - radiusFromCenter * 2.0;
      gl_FragColor = vec4(vec3(0.82, 0.90, 1.0) * glow, glow);
    }
  `;

  function yuruyurauVertexShader(figureBody) {
    return `
      precision highp float;
      attribute float a_point_index;
      uniform float u_time;
      uniform vec2 u_clip;
      uniform float u_point_size;
      void main() {
        float i = a_point_index;
        ${figureBody}
        gl_Position = vec4(x * u_clip.x, y * u_clip.y, 0.0, 1.0);
        gl_PointSize = u_point_size;
      }
    `;
  }

  const figureBodyByVariant = {
    twin: `
      float parity = mod(i, 2.0) * 9.0;
      float k = 9.0 * cos(i / 81.0);
      float e = i / 765.0 - 13.0;
      float d = length(vec2(k, e)) / 4.0;
      float outerBranch = step(19.0, k * k);
      float inner = mix(u_time * 3.0 + d * 4.0, d / 2.0 + 4.0, outerBranch);
      float q = 79.0 - 2.0 * sin(k * 3.0)
        + sin(inner) / 2.0 * k * (9.0 + 5.0 * sin(d * d - e / 6.0 - u_time + parity));
      float c = d * d / 9.0 - u_time / 16.0 + parity;
      float x = q * sin(c);
      float y = (q + 50.0) * cos(c);
    `,
    solo: `
      float k = 9.0 * cos(i / 81.0);
      float e = i / 765.0 - 13.0;
      float d = length(vec2(k, e)) / 4.0;
      float outerBranch = step(19.0, k * k);
      float inner = mix(u_time * 3.0 + d * 4.0, d / 2.0 + 4.0, outerBranch);
      float q = 79.0 - 2.0 * sin(k * 3.0)
        + sin(inner) / 2.0 * k * (9.0 + 5.0 * sin(d * d - e / 6.0 - u_time));
      float c = d * d / 9.0 - u_time / 16.0;
      float x = q * sin(c);
      float y = (q + 50.0) * cos(c);
    `,
    swirl: `
      float k = 9.0 * cos(i / 81.0);
      float e = i / 765.0 - 13.0;
      float d = length(vec2(k, e)) / 4.0;
      float outerBranch = step(19.0, k * k);
      float inner = mix(u_time * 3.0 + d * 4.0, d / 2.0 + 4.0, outerBranch);
      float q = 79.0 - 2.0 * sin(k * 3.0)
        + sin(inner) / 2.0 * k * (9.0 + 5.0 * sin(d * d / 2.0 - e / 6.0 - u_time));
      float c = d * d / 12.0 - u_time / 16.0;
      float x = q * sin(c);
      float y = (q + 50.0) * cos(c);
    `,
    petal: `
      float k = 9.0 * cos(i / 60.0);
      float e = i / 500.0 - 13.0;
      float d = length(vec2(k, e)) / 4.0;
      float outerBranch = step(19.0, k * k);
      float inner = mix(u_time * 2.0 + d * 3.0, d / 2.0 + 4.0, outerBranch);
      float q = 64.0 - 2.0 * sin(k * 4.0)
        + sin(inner) / 2.0 * k * (9.0 + 5.0 * sin(d * d - e / 6.0 - u_time));
      float c = d * d / 9.0 - u_time / 16.0;
      float x = q * sin(c);
      float y = (q + 50.0) * cos(c);
    `,
  };

  const figureExtentByVariant = {
    twin: 150.0,
    solo: 150.0,
    swirl: 150.0,
    petal: 130.0,
  };

  const YURUYURAU_POINT_COUNT = 20000;
  const FIGURE_FILL_RATIO = 0.44;
  const TIME_STEP_PER_SECOND = ((2.0 * Math.PI) / 45.0) * 15.0;

  function compileShader(gl, shaderType, shaderSource) {
    const shader = gl.createShader(shaderType);
    gl.shaderSource(shader, shaderSource);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error(
        "ambient-canvas yuruyurau shader failed to compile: " +
          gl.getShaderInfoLog(shader),
      );
    }
    return shader;
  }

  function createYuruyurauRenderer(canvasElement, options) {
    const gl = canvasElement.getContext("webgl", {
      antialias: true,
      alpha: false,
      preserveDrawingBuffer:
        (options && options.preserveDrawingBuffer) || false,
    });
    if (!gl) {
      console.error("ambient-canvas: WebGL unavailable for a yuruyurau pane");
      return { render() {}, resize() {} };
    }
    const variantNames = Object.keys(figureBodyByVariant);
    const selectedVariant =
      (options && options.variant) ||
      variantNames[Math.floor(Math.random() * variantNames.length)];
    const figureExtent = figureExtentByVariant[selectedVariant];
    const devicePixelRatio = (options && options.devicePixelRatio) || 1;

    const program = gl.createProgram();
    gl.attachShader(
      program,
      compileShader(
        gl,
        gl.VERTEX_SHADER,
        yuruyurauVertexShader(figureBodyByVariant[selectedVariant]),
      ),
    );
    gl.attachShader(
      program,
      compileShader(gl, gl.FRAGMENT_SHADER, sharedFragmentShaderSource),
    );
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error(
        "ambient-canvas yuruyurau program failed to link: " +
          gl.getProgramInfoLog(program),
      );
    }

    const pointIndices = new Float32Array(YURUYURAU_POINT_COUNT);
    for (let position = 0; position < YURUYURAU_POINT_COUNT; position += 1) {
      pointIndices[position] = position + 1;
    }
    const pointIndexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, pointIndexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, pointIndices, gl.STATIC_DRAW);

    const pointIndexAttribute = gl.getAttribLocation(program, "a_point_index");
    const timeUniform = gl.getUniformLocation(program, "u_time");
    const clipUniform = gl.getUniformLocation(program, "u_clip");
    const pointSizeUniform = gl.getUniformLocation(program, "u_point_size");

    gl.clearColor(0.039, 0.102, 0.184, 1.0);
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
    };
  }

  window.AMBIENT_CANVAS_SCENE_FACTORIES =
    window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
  window.AMBIENT_CANVAS_SCENE_FACTORIES["yuruyurau"] = createYuruyurauRenderer;
})();
