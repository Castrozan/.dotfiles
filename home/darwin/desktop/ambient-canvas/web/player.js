(function runAmbientCanvasPlayer() {
  const surface = document.getElementById("ambient-canvas-surface");
  const gl = surface.getContext("webgl", { antialias: true, alpha: false });
  const scenes = window.AMBIENT_CANVAS_SCENES || [];
  const fragmentShaderSource = window.AMBIENT_CANVAS_FRAGMENT_SHADER;

  const FIGURE_FILL_RATIO = 0.44;
  const TIME_STEP_PER_SECOND = ((2.0 * Math.PI) / 45.0) * 15.0;
  const SCENE_ROTATION_SECONDS = 40.0;
  const BACKGROUND_COLOR = [0.039, 0.102, 0.184];

  if (!gl || scenes.length === 0) {
    return;
  }

  function compileShader(shaderType, shaderSource) {
    const shader = gl.createShader(shaderType);
    gl.shaderSource(shader, shaderSource);
    gl.compileShader(shader);
    return shader;
  }

  function buildCompiledScene(scene) {
    const program = gl.createProgram();
    gl.attachShader(
      program,
      compileShader(gl.VERTEX_SHADER, scene.vertexShaderSource),
    );
    gl.attachShader(
      program,
      compileShader(gl.FRAGMENT_SHADER, fragmentShaderSource),
    );
    gl.linkProgram(program);

    const pointIndices = new Float32Array(scene.pointCount);
    for (let position = 0; position < scene.pointCount; position += 1) {
      pointIndices[position] = position + 1;
    }
    const pointIndexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, pointIndexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, pointIndices, gl.STATIC_DRAW);

    return {
      scene: scene,
      program: program,
      pointIndexBuffer: pointIndexBuffer,
      pointIndexAttribute: gl.getAttribLocation(program, "a_point_index"),
      timeUniform: gl.getUniformLocation(program, "u_time"),
      clipUniform: gl.getUniformLocation(program, "u_clip"),
      pointSizeUniform: gl.getUniformLocation(program, "u_point_size"),
    };
  }

  const compiledScenes = scenes.map(buildCompiledScene);

  let currentDevicePixelRatio = window.devicePixelRatio || 1;
  function resizeSurface() {
    currentDevicePixelRatio = window.devicePixelRatio || 1;
    surface.width = Math.floor(window.innerWidth * currentDevicePixelRatio);
    surface.height = Math.floor(window.innerHeight * currentDevicePixelRatio);
    gl.viewport(0, 0, surface.width, surface.height);
  }
  window.addEventListener("resize", resizeSurface);
  resizeSurface();

  gl.clearColor(
    BACKGROUND_COLOR[0],
    BACKGROUND_COLOR[1],
    BACKGROUND_COLOR[2],
    1.0,
  );
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE);

  let currentSceneIndex = Math.floor(Math.random() * compiledScenes.length);
  let animationTime = 0.0;
  let currentSceneElapsedSeconds = 0.0;
  let previousTimestampMilliseconds = null;

  function advanceToAnotherScene() {
    if (compiledScenes.length <= 1) {
      return;
    }
    let nextSceneIndex = currentSceneIndex;
    while (nextSceneIndex === currentSceneIndex) {
      nextSceneIndex = Math.floor(Math.random() * compiledScenes.length);
    }
    currentSceneIndex = nextSceneIndex;
    animationTime = 0.0;
  }

  function renderFrame(timestampMilliseconds) {
    if (previousTimestampMilliseconds === null) {
      previousTimestampMilliseconds = timestampMilliseconds;
    }
    const deltaSeconds = Math.min(
      (timestampMilliseconds - previousTimestampMilliseconds) / 1000.0,
      0.1,
    );
    previousTimestampMilliseconds = timestampMilliseconds;

    animationTime += TIME_STEP_PER_SECOND * deltaSeconds;
    currentSceneElapsedSeconds += deltaSeconds;
    if (currentSceneElapsedSeconds >= SCENE_ROTATION_SECONDS) {
      currentSceneElapsedSeconds = 0.0;
      advanceToAnotherScene();
    }

    const compiled = compiledScenes[currentSceneIndex];
    const minimumDimension = Math.min(surface.width, surface.height);
    const pixelScale =
      (FIGURE_FILL_RATIO * minimumDimension) / compiled.scene.figureExtent;

    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(compiled.program);
    gl.bindBuffer(gl.ARRAY_BUFFER, compiled.pointIndexBuffer);
    gl.enableVertexAttribArray(compiled.pointIndexAttribute);
    gl.vertexAttribPointer(
      compiled.pointIndexAttribute,
      1,
      gl.FLOAT,
      false,
      0,
      0,
    );
    gl.uniform1f(compiled.timeUniform, animationTime);
    gl.uniform2f(
      compiled.clipUniform,
      pixelScale / (surface.width / 2),
      pixelScale / (surface.height / 2),
    );
    gl.uniform1f(
      compiled.pointSizeUniform,
      Math.max(1.0, 1.6 * currentDevicePixelRatio),
    );
    gl.drawArrays(gl.POINTS, 0, compiled.scene.pointCount);

    window.requestAnimationFrame(renderFrame);
  }

  window.requestAnimationFrame(renderFrame);
})();
