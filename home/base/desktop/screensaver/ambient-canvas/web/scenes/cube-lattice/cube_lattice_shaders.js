window.AmbientCanvasCubeLatticeShaders = (function buildCubeLatticeShaders() {
  const vertexShaderSource = `
    precision highp float;
    attribute vec2 a_clip_position;

    void main() {
      gl_Position = vec4(a_clip_position, 0.0, 1.0);
    }
  `;

  const fragmentShaderSource = `
    precision highp float;
    uniform vec2 u_resolution;
    uniform float u_time;

    const float cellSize = 1.0;
    const float cubeHalfExtent = 0.27;
    const float frameThickness = 0.002;
    const float fisheyeRadiansPerScreenUnit = 2.35;
    const float secondsPerCellTravelled = 3.0;
    const int marchStepCount = 176;
    const float marchStepScale = 0.85;
    const float minimumMarchStep = 0.006;
    const float marchStepGrowth = 0.006;
    const float maximumMarchDistance = 7.0;
    const float wireRadiansOnScreen = 0.0016;
    const float fogDensity = 0.55;
    const vec3 neonGreenResponse = vec3(0.55, 3.10, 0.95);

    float cubeFrameDistance(vec3 position) {
      vec3 outside = abs(position) - cubeHalfExtent;
      vec3 inset = abs(outside + frameThickness) - frameThickness;
      float alongX =
        length(max(vec3(outside.x, inset.y, inset.z), 0.0)) +
        min(max(outside.x, max(inset.y, inset.z)), 0.0);
      float alongY =
        length(max(vec3(inset.x, outside.y, inset.z), 0.0)) +
        min(max(inset.x, max(outside.y, inset.z)), 0.0);
      float alongZ =
        length(max(vec3(inset.x, inset.y, outside.z), 0.0)) +
        min(max(inset.x, max(inset.y, outside.z)), 0.0);
      return min(alongX, min(alongY, alongZ));
    }

    float latticeDistance(vec3 position) {
      vec3 cell =
        mod(position + 0.5 * cellSize, cellSize) - 0.5 * cellSize;
      return cubeFrameDistance(cell);
    }

    vec3 fisheyeRayDirection(vec2 screenOffset) {
      float screenRadius = length(screenOffset);
      vec2 bearing =
        screenRadius > 0.0 ? screenOffset / screenRadius : vec2(0.0, 0.0);
      float coneAngle = screenRadius * fisheyeRadiansPerScreenUnit;
      return vec3(bearing * sin(coneAngle), cos(coneAngle));
    }

    float nearestWireResponse(vec3 rayOrigin, vec3 rayDirection) {
      float travelled = 0.0;
      float brightest = 0.0;
      for (int marchIndex = 0; marchIndex < marchStepCount; marchIndex += 1) {
        if (travelled > maximumMarchDistance) {
          break;
        }
        float distanceToLattice =
          latticeDistance(rayOrigin + rayDirection * travelled);
        float wireHalfWidth =
          max(wireRadiansOnScreen * travelled, minimumMarchStep);
        float widthsFromWire = max(distanceToLattice, 0.0) / wireHalfWidth;
        brightest = max(
          brightest,
          exp(-widthsFromWire * widthsFromWire - travelled * fogDensity)
        );
        travelled += max(
          distanceToLattice * marchStepScale,
          minimumMarchStep + travelled * marchStepGrowth
        );
      }
      return brightest;
    }

    void main() {
      vec2 screenOffset =
        (gl_FragCoord.xy - 0.5 * u_resolution) / u_resolution.y;
      vec3 rayOrigin =
        vec3(0.0, 0.0, u_time * cellSize / secondsPerCellTravelled);
      float glow =
        nearestWireResponse(rayOrigin, fisheyeRayDirection(screenOffset));
      gl_FragColor = vec4(1.0 - exp(-glow * neonGreenResponse), 1.0);
    }
  `;

  return { vertexShaderSource, fragmentShaderSource };
})();
