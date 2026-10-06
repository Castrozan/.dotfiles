window.AmbientCanvasYuruyurauSetup = (function buildYuruyurauSetup() {
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

  function createYuruyurauProgram(gl, selectedVariant) {
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
    return program;
  }

  function createPointIndexBuffer(gl, pointCount) {
    const pointIndices = new Float32Array(pointCount);
    for (let position = 0; position < pointCount; position += 1) {
      pointIndices[position] = position + 1;
    }
    const pointIndexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, pointIndexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, pointIndices, gl.STATIC_DRAW);
    return pointIndexBuffer;
  }

  return {
    createProgram: createYuruyurauProgram,
    createPointIndexBuffer,
  };
})();
