window.AmbientCanvasExtradiegeticShaders =
  (function buildExtradiegeticShaders() {
    const mainSource = `
    void main() {
      vec2 lattice = particleLattice(a_point_index);
      float population = hashed(lattice, 0.0);
      PlacedParticle placed;

      if (population < beamPopulationShare) {
        placed = placeBeamParticle(lattice);
      } else if (population < streakPopulationShare) {
        placed = placeStreakParticle(lattice);
      } else if (population < topBandPopulationShare) {
        placed = placeTopBandParticle(lattice);
      } else if (population < middleBandPopulationShare) {
        placed = placeMiddleBandParticle(lattice);
      } else {
        placed = placeEyeParticle(lattice);
      }

      v_brightness = placed.brightness;
      v_streak_axis = placed.streakAxis;
      v_anisotropy = placed.anisotropy;

      if (hashed(lattice, 20.0) > clamp(placed.luminance, 0.0, 1.0)) {
        gl_Position = vec4(2.0, 2.0, 0.0, 1.0);
        gl_PointSize = 1.0;
        v_brightness = 0.0;
        return;
      }

      gl_Position = vec4(placed.position.x / u_aspect, placed.position.y, 0.0, 1.0);
      gl_PointSize = max(1.0, u_point_size * placed.pointScale);
    }
  `;

    const vertexShaderSource =
      window.AmbientCanvasExtradiegeticFieldGlsl +
      window.AmbientCanvasExtradiegeticPanelGlsl +
      mainSource;

    const fragmentShaderSource = `
    precision mediump float;
    varying float v_brightness;
    varying vec2 v_streak_axis;
    varying vec2 v_anisotropy;
    void main() {
      vec2 offsetFromCentre = (gl_PointCoord - vec2(0.5)) * 2.0;
      vec2 alongAxis = normalize(v_streak_axis);
      vec2 acrossAxis = vec2(-alongAxis.y, alongAxis.x);
      float lengthwise = dot(offsetFromCentre, alongAxis);
      float widthwise = dot(offsetFromCentre, acrossAxis);
      float falloff = 1.0 - clamp(
        lengthwise * lengthwise * v_anisotropy.x +
          widthwise * widthwise * v_anisotropy.y,
        0.0,
        1.0
      );
      if (falloff <= 0.0) {
        discard;
      }
      float glow = falloff * v_brightness;
      gl_FragColor = vec4(vec3(glow), glow);
    }
  `;

    return { vertexShaderSource, fragmentShaderSource };
  })();
