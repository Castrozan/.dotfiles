window.AmbientCanvasTheLinkShaders = (function buildTheLinkShaders() {
  const vertexShaderSource = `
    precision highp float;
    attribute float a_point_index;
    uniform float u_time;
    uniform float u_aspect;
    uniform float u_dome_radius;
    uniform float u_waist_gap;
    uniform float u_point_size;
    varying float v_brightness;
    varying vec2 v_streak_axis;

    const float beamPopulationShare = 0.020;
    const float waistPopulationShare = 0.042;
    const float sprayPopulationShare = 0.150;
    const float fieldCeiling = 1.06;
    const float beamReach = 1.45;

    vec2 particleLattice(float index) {
      return vec2(mod(index, 509.0), floor(index / 509.0));
    }

    float hashed(vec2 lattice, float salt) {
      vec3 seed = fract(
        vec3(
          lattice.x + salt * 37.0,
          lattice.y + salt * 91.0,
          lattice.x + salt * 53.0
        ) * 0.1031
      );
      seed += dot(seed, seed.yzx + 33.33);
      return fract((seed.x + seed.y) * seed.z);
    }

    float domeArcHeight(float horizontal) {
      float squaredReach =
        u_dome_radius * u_dome_radius - horizontal * horizontal;
      return u_dome_radius - sqrt(max(squaredReach, 0.0));
    }

    vec2 turned(vec2 axis, float angle) {
      float cosine = cos(angle);
      float sine = sin(angle);
      return vec2(
        axis.x * cosine - axis.y * sine,
        axis.x * sine + axis.y * cosine
      );
    }

    void main() {
      vec2 lattice = particleLattice(a_point_index);
      float population = hashed(lattice, 0.0);
      float side = hashed(lattice, 1.0) < 0.5 ? 1.0 : -1.0;
      vec2 position;
      vec2 streakAxis;
      float brightness;
      float pointScale;

      if (population < beamPopulationShare) {
        float beamSide = hashed(lattice, 12.0) < 0.86 ? 1.0 : -1.0;
        float travel = fract(
          hashed(lattice, 6.0) + u_time * (0.03 + 0.10 * hashed(lattice, 7.0))
        );
        float height = pow(travel, 0.85) * beamReach;
        float sway = sin(height * 2.4 + u_time * 0.6) * 0.010 * height;
        position = vec2(
          sway + (hashed(lattice, 8.0) - 0.5) * (0.003 + 0.011 * height),
          beamSide * (u_waist_gap + height)
        );
        streakAxis = vec2(0.05, 1.0);
        brightness = (1.0 - height / (beamReach + 0.35))
          * (beamSide > 0.0 ? 3.2 : 0.7);
        pointScale = 0.8;
      } else if (population < waistPopulationShare) {
        float spread = pow(hashed(lattice, 9.0), 0.45);
        position = vec2(
          (hashed(lattice, 10.0) - 0.5) * 0.21 * spread,
          (hashed(lattice, 11.0) - 0.5) * 0.032 * (1.0 - 0.6 * spread)
        );
        streakAxis = vec2(1.0, 0.09);
        brightness = (1.3 - spread)
          * (0.78 + 0.30 * sin(u_time * 1.7 + spread * 6.0)) * 2.6;
        pointScale = 0.85;
      } else {
        float horizontal = (hashed(lattice, 2.0) * 2.0 - 1.0) * u_aspect;
        float arc = domeArcHeight(horizontal);
        float fall = fract(
          hashed(lattice, 3.0) - u_time * (0.004 + 0.022 * hashed(lattice, 4.0))
        );
        vec2 outward =
          vec2(horizontal, side * (arc - u_dome_radius)) / u_dome_radius;
        streakAxis = turned(outward, (hashed(lattice, 14.0) - 0.5) * 0.5);
        pointScale = 0.75 + 0.55 * hashed(lattice, 13.0);
        if (population < sprayPopulationShare) {
          float sprayReach = pow(fall, 2.6) * (0.10 + 0.42 * arc);
          position = vec2(horizontal, side * (u_waist_gap + arc - sprayReach));
          brightness =
            1.9 * (1.0 - 0.5 * fall) * (0.4 + 0.9 * hashed(lattice, 5.0));
        } else {
          float span = max(fieldCeiling - arc, 0.18);
          float depth = pow(fall, 1.25) * span;
          position = vec2(horizontal, side * (u_waist_gap + arc + depth));
          brightness = mix(2.8, 0.30, pow(fall, 0.35))
            * (0.55 + 0.8 * hashed(lattice, 5.0));
        }
      }

      gl_Position = vec4(position.x / u_aspect, position.y, 0.0, 1.0);
      gl_PointSize = max(1.0, u_point_size * pointScale);
      v_brightness = max(brightness, 0.0);
      v_streak_axis = streakAxis;
    }
  `;

  const fragmentShaderSource = `
    precision mediump float;
    varying float v_brightness;
    varying vec2 v_streak_axis;
    void main() {
      vec2 offsetFromCenter = (gl_PointCoord - vec2(0.5)) * 2.0;
      vec2 alongAxis = normalize(v_streak_axis);
      vec2 acrossAxis = vec2(-alongAxis.y, alongAxis.x);
      float lengthwise = dot(offsetFromCenter, alongAxis);
      float widthwise = dot(offsetFromCenter, acrossAxis);
      float falloff = 1.0 - clamp(
        lengthwise * lengthwise * 0.5 + widthwise * widthwise * 3.2,
        0.0,
        1.0
      );
      if (falloff <= 0.0) {
        discard;
      }
      float glow = falloff * falloff * v_brightness;
      gl_FragColor = vec4(vec3(glow), glow);
    }
  `;

  return { vertexShaderSource, fragmentShaderSource };
})();
