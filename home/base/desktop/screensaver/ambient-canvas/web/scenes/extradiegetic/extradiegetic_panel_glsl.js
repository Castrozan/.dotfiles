window.AmbientCanvasExtradiegeticPanelGlsl = `
  PlacedParticle placeBeamParticle(vec2 lattice) {
    PlacedParticle placed;
    placed.streakAxis = vec2(1.0, 0.0);
    placed.anisotropy = vec2(2.2, 2.2);
    placed.luminance = 2.0;
    placed.pointScale = 1.0;
    float toTheRight = hashed(lattice, 1.0) < 0.5 ? 1.0 : 0.0;
    float beamColumn = mix(-beamFraction, beamFraction, toTheRight) * u_aspect;
    float originHeight = mix(
      leftBeamOriginHeight,
      rightBeamOriginHeight,
      toTheRight
    );
    float along = hashed(lattice, 2.0);
    if (along < originDotShare) {
      float angle = hashed(lattice, 3.0) * fullTurn;
      float radius = sqrt(hashed(lattice, 4.0)) * originDotRadius;
      placed.position = vec2(
        beamColumn + cos(angle) * radius,
        originHeight + sin(angle) * radius
      );
      placed.brightness = 5.4;
      placed.pointScale = 1.7;
      return placed;
    }
    float descent = (along - originDotShare) / (1.0 - originDotShare);
    placed.position = vec2(
      beamColumn + (hashed(lattice, 5.0) - 0.5) * 0.0045,
      mix(originHeight, streakHeight, descent)
    );
    placed.brightness = 0.85 + 2.6 * travellingPulse(descent, toTheRight * 0.37);
    placed.streakAxis = vec2(0.0, 1.0);
    placed.anisotropy = vec2(0.28, 6.4);
    return placed;
  }

  PlacedParticle placeStreakParticle(vec2 lattice) {
    PlacedParticle placed;
    float span = hashed(lattice, 6.0) * 2.0 - 1.0;
    placed.position = vec2(
      eyeCenterFraction * u_aspect + span * (eyeHalfWidth + 0.34),
      streakHeight + (hashed(lattice, 7.0) - 0.5) * 0.0055
    );
    float landing =
      exp(-pow(abs(abs(span) - 0.58), 2.0) * 26.0) *
      (0.6 + 0.5 * sin(u_time * 0.85));
    placed.brightness = 0.7 + 2.4 * (1.0 - abs(span)) + 2.1 * landing;
    placed.streakAxis = vec2(1.0, 0.0);
    placed.anisotropy = vec2(0.30, 6.0);
    placed.luminance = 2.0;
    placed.pointScale = 1.0;
    return placed;
  }

  PlacedParticle placeTopBandParticle(vec2 lattice) {
    PlacedParticle placed;
    float horizontal = mix(
      -u_aspect,
      topBandRightFraction * u_aspect,
      hashed(lattice, 8.0)
    );
    float height = mix(topBandBottom, 1.0, hashed(lattice, 9.0));
    placed.position = vec2(horizontal, height);
    float acrossStrip = horizontal / u_aspect;
    float creaseLine =
      0.79 - 0.09 * acrossStrip - 0.07 * acrossStrip * acrossStrip;
    float crease = exp(-pow(height - creaseLine, 2.0) * 820.0);
    float lashLine = exp(-pow(height - creaseLine + 0.048, 2.0) * 2600.0);
    float skin =
      0.34 + 0.54 * smoothstep(topBandBottom, 0.75, height) -
      0.20 * smoothstep(0.90, 1.0, height);
    placed.luminance =
      (skin * (1.0 - 0.90 * crease) + 0.60 * lashLine) *
      (1.0 - 0.22 * smoothstep(-0.2, topBandRightFraction, acrossStrip));
    placed.brightness = 0.85;
    placed.streakAxis = vec2(1.0, 0.0);
    placed.anisotropy = vec2(2.7, 2.7);
    placed.pointScale = 1.2;
    return placed;
  }

  PlacedParticle placeMiddleBandParticle(vec2 lattice) {
    PlacedParticle placed;
    placed.streakAxis = vec2(1.0, 0.0);
    placed.anisotropy = vec2(2.7, 2.7);
    placed.pointScale = 1.0;
    vec2 sphereCentre =
      vec2(sphereCenterFraction * u_aspect, sphereCenterHeight);
    float role = hashed(lattice, 10.0);
    if (role < 0.56) {
      float angle = hashed(lattice, 11.0) * fullTurn;
      float radius = sqrt(hashed(lattice, 12.0)) * u_sphere_radius;
      placed.position = sphereCentre + vec2(cos(angle), sin(angle)) * radius;
      float towardsRim = radius / u_sphere_radius;
      placed.luminance = 1.12 - 0.55 * towardsRim * towardsRim;
      placed.brightness = 0.9 + 0.7 * (1.0 - towardsRim);
      placed.pointScale = 0.95 + 0.55 * (1.0 - towardsRim);
    } else if (role < 0.84) {
      float sweep = 3.25 + hashed(lattice, 13.0) * 3.15;
      float reach = 1.02 + hashed(lattice, 14.0) * 0.55;
      placed.position =
        sphereCentre + vec2(cos(sweep), sin(sweep)) * u_sphere_radius * reach;
      float outward = (reach - 1.02) / 0.55;
      placed.luminance = 0.60 * pow(1.0 - outward, 1.5);
      placed.brightness = 0.78;
    } else {
      placed.position = vec2(
        (hashed(lattice, 15.0) * 2.0 - 1.0) * u_aspect,
        mix(middleBandBottom, middleBandTop, hashed(lattice, 16.0))
      );
      placed.luminance = 0.055;
      placed.brightness = 0.6 + 0.9 * hashed(lattice, 17.0);
    }
    if (placed.position.y > middleBandTop ||
        placed.position.y < middleBandBottom) {
      placed.luminance = 0.0;
    }
    return placed;
  }

  PlacedParticle placeEyeParticle(vec2 lattice) {
    PlacedParticle placed;
    float eyeCentre = eyeCenterFraction * u_aspect;
    float horizontal = (hashed(lattice, 18.0) * 2.0 - 1.0) * eyeHalfWidth;
    float lidProfile =
      1.0 - horizontal * horizontal / (eyeHalfWidth * eyeHalfWidth);
    placed.position = vec2(
      eyeCentre + horizontal,
      mix(
        streakHeight - eyeLidDrop * lidProfile,
        streakHeight + eyeLidRise * lidProfile,
        hashed(lattice, 19.0)
      )
    );
    float radial = length(placed.position - vec2(eyeCentre, streakHeight));
    float outsidePupil =
      smoothstep(u_pupil_radius, u_pupil_radius * 1.06, radial);
    float halo = exp(-pow(radial - u_pupil_radius * 1.30, 2.0) * 55.0);
    placed.luminance =
      outsidePupil * (0.50 + 0.85 * halo) * pow(max(lidProfile, 0.0), 0.30);
    placed.brightness = 0.85 + 1.90 * halo;
    placed.streakAxis = vec2(1.0, 0.0);
    placed.anisotropy = vec2(2.7, 2.7);
    placed.pointScale = 1.0 + 1.35 * halo;
    return placed;
  }
`;
