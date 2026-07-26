window.AmbientCanvasExtradiegeticFieldGlsl = `
  precision highp float;
  attribute float a_point_index;
  uniform float u_time;
  uniform float u_aspect;
  uniform float u_sphere_radius;
  uniform float u_pupil_radius;
  uniform float u_point_size;
  varying float v_brightness;
  varying vec2 v_streak_axis;
  varying vec2 v_anisotropy;

  const float beamPopulationShare = 0.034;
  const float streakPopulationShare = 0.056;
  const float topBandPopulationShare = 0.310;
  const float middleBandPopulationShare = 0.620;

  const float topBandBottom = 0.52;
  const float topBandRightFraction = 0.36;
  const float middleBandTop = 0.44;
  const float middleBandBottom = -0.30;

  const float beamFraction = 0.64;
  const float leftBeamOriginHeight = 0.74;
  const float rightBeamOriginHeight = 0.66;
  const float streakHeight = -0.70;
  const float originDotShare = 0.12;
  const float originDotRadius = 0.013;

  const float eyeCenterFraction = 0.05;
  const float eyeHalfWidth = 1.30;
  const float eyeLidRise = 0.30;
  const float eyeLidDrop = 0.252;
  const float sphereCenterFraction = -0.13;
  const float sphereCenterHeight = 0.05;

  const float fullTurn = 6.2831853;

  struct PlacedParticle {
    vec2 position;
    vec2 streakAxis;
    vec2 anisotropy;
    float luminance;
    float brightness;
    float pointScale;
  };

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

  float travellingPulse(float along, float phase) {
    float offset = along - fract(u_time * 0.16 + phase);
    return exp(-offset * offset * 240.0);
  }
`;
