(function registerYuruyurauScenes() {
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

  const twinFigureBody = `
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
  `;

  const soloFigureBody = `
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
  `;

  const swirlFigureBody = `
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
  `;

  const petalFigureBody = `
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
  `;

  window.AMBIENT_CANVAS_FRAGMENT_SHADER = sharedFragmentShaderSource;
  window.AMBIENT_CANVAS_SCENES = [
    {
      name: "twin",
      pointCount: 20000,
      figureExtent: 150.0,
      vertexShaderSource: yuruyurauVertexShader(twinFigureBody),
    },
    {
      name: "solo",
      pointCount: 20000,
      figureExtent: 150.0,
      vertexShaderSource: yuruyurauVertexShader(soloFigureBody),
    },
    {
      name: "swirl",
      pointCount: 20000,
      figureExtent: 150.0,
      vertexShaderSource: yuruyurauVertexShader(swirlFigureBody),
    },
    {
      name: "petal",
      pointCount: 20000,
      figureExtent: 130.0,
      vertexShaderSource: yuruyurauVertexShader(petalFigureBody),
    },
  ];
})();
