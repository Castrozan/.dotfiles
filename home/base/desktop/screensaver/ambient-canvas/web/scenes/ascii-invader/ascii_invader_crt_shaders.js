window.AmbientCanvasAsciiInvaderCrtShaders =
  (function buildAsciiInvaderCrtShaders() {
    const vertexShaderSource = `
    precision highp float;
    attribute vec2 a_screen_corner;
    varying vec2 v_screen_uv;
    void main() {
      v_screen_uv = a_screen_corner * 0.5 + 0.5;
      gl_Position = vec4(a_screen_corner, 0.0, 1.0);
    }
  `;

    const fragmentShaderSource = `
    precision highp float;
    uniform sampler2D u_glyph_field;
    uniform float u_time;
    uniform vec2 u_resolution;
    uniform float u_pane_aspect;
    varying vec2 v_screen_uv;

    const float screenSideInHeights = 0.92;

    const float barrelStrength = 0.085;
    const float bezelRadius = 0.055;
    const float scanlineDepth = 0.13;
    const float bloomRadius = 0.0055;
    const float burstsPerSecond = 2.4;

    float hashedSlot(float slot, float salt) {
      float folded = mod(slot, 512.0);
      vec3 seed = fract(
        vec3(folded + salt * 3.7, salt * 9.1, folded * 0.37 + salt) * 0.1031
      );
      seed += dot(seed, seed.yzx + 33.33);
      return fract((seed.x + seed.y) * seed.z);
    }

    vec2 curveScreen(vec2 uv) {
      vec2 centred = uv * 2.0 - 1.0;
      centred *= 1.0 + dot(centred, centred) * barrelStrength;
      return centred * 0.5 + 0.5;
    }

    float bezelMask(vec2 uv) {
      vec2 fromCentre = abs(uv - 0.5) * 2.0;
      vec2 corner = max(fromCentre - (1.0 - bezelRadius * 2.0), 0.0);
      float cornerReach = length(corner) / (bezelRadius * 2.0);
      float inside = 1.0 - smoothstep(0.85, 1.0, cornerReach);
      float edges =
        step(fromCentre.x, 1.0) * step(fromCentre.y, 1.0);
      return inside * edges;
    }

    float burstIntensity() {
      float slot = floor(u_time * burstsPerSecond);
      float chance = hashedSlot(slot, 3.0);
      if (chance > 0.20) {
        return 0.0;
      }
      float withinSlot = fract(u_time * burstsPerSecond);
      return (1.0 - withinSlot) * (0.45 + 0.55 * hashedSlot(slot, 5.0));
    }

    vec2 glitchedSample(vec2 uv, float burst) {
      if (burst <= 0.0) {
        return uv;
      }
      float band = floor(uv.y * 42.0);
      float slot = floor(u_time * burstsPerSecond);
      float shove = hashedSlot(band + slot * 17.0, 13.0) - 0.5;
      float engaged = step(0.62, hashedSlot(band + slot * 23.0, 19.0));
      return vec2(uv.x + shove * 0.10 * burst * engaged, uv.y);
    }

    vec3 bloomedSample(vec2 uv, float channelOffset) {
      vec3 gathered = vec3(0.0);
      gathered.r = texture2D(u_glyph_field, uv + vec2(channelOffset, 0.0)).r;
      gathered.g = texture2D(u_glyph_field, uv).g;
      gathered.b = texture2D(u_glyph_field, uv - vec2(channelOffset, 0.0)).b;
      vec3 halo = vec3(0.0);
      for (int tap = 0; tap < 8; tap += 1) {
        float angle = float(tap) * 0.7853981;
        vec2 offset = vec2(cos(angle), sin(angle)) * bloomRadius;
        halo += texture2D(u_glyph_field, uv + offset).rgb;
      }
      return gathered + halo * 0.085;
    }

    vec3 glitchBands(vec2 uv, float burst, float slot) {
      if (burst <= 0.0) {
        return vec3(0.0);
      }
      vec3 laid = vec3(0.0);
      for (int bandIndex = 0; bandIndex < 3; bandIndex += 1) {
        float seed = float(bandIndex) + slot * 7.0;
        float centre = hashedSlot(seed, 29.0);
        float thickness = 0.012 + hashedSlot(seed, 31.0) * 0.055;
        float covered = step(abs(uv.y - centre), thickness);
        vec3 tint = vec3(
          hashedSlot(seed, 37.0),
          hashedSlot(seed, 41.0),
          hashedSlot(seed, 43.0)
        );
        laid += covered * tint * 0.40 * burst;
      }
      return laid;
    }

    void main() {
      vec2 acrossPane = (v_screen_uv - 0.5) * vec2(u_pane_aspect, 1.0);
      vec2 screenUv = acrossPane / screenSideInHeights + 0.5;
      if (screenUv.x < 0.0 || screenUv.x > 1.0 ||
          screenUv.y < 0.0 || screenUv.y > 1.0) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
      }

      vec2 curved = curveScreen(screenUv);
      float mask = bezelMask(curved);
      if (mask <= 0.0) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
      }

      float burst = burstIntensity();
      float slot = floor(u_time * burstsPerSecond);
      vec2 sampled = glitchedSample(curved, burst);
      float channelOffset = 0.0009 + 0.0032 * burst;
      vec3 colour = bloomedSample(sampled, channelOffset);

      colour += glitchBands(curved, burst, slot);

      float scanline =
        1.0 - scanlineDepth * (0.5 + 0.5 * sin(curved.y * u_resolution.y * 1.57));
      colour *= scanline;

      vec2 fromCentre = curved - 0.5;
      float vignette = 1.0 - dot(fromCentre, fromCentre) * 1.15;
      colour *= clamp(vignette, 0.0, 1.0);

      gl_FragColor = vec4(colour * mask, 1.0);
    }
  `;

    return { vertexShaderSource, fragmentShaderSource };
  })();
