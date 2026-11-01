const EMOTION_MORPH_SUFFIXES = {
  happy: "Joy",
  angry: "Angry",
  sad: "Sorrow",
  relaxed: "Fun",
  Surprised: "Surprised",
};

class MorphBind {
  constructor(meshes, index) {
    this.meshes = meshes;
    this.index = index;
  }

  applyWeight(weight) {
    for (const mesh of this.meshes) mesh.morphTargetInfluences[this.index] += weight;
  }

  clearAppliedWeight() {
    for (const mesh of this.meshes) mesh.morphTargetInfluences[this.index] = 0;
  }
}

export function emotionMouthName(emotion) {
  return `${emotion}Mouth`;
}

export function separateEmotionMouths(vrm, createExpression) {
  const faceMeshes = [];
  vrm.scene.traverse((node) => {
    if (node.morphTargetDictionary?.Fcl_MTH_A !== undefined)
      faceMeshes.push(node);
  });
  const manager = vrm.expressionManager;
  const registerMorphExpression = (name, morphNames) => {
    const expression = createExpression(name);
    for (const morphName of morphNames)
      expression.addBind(
        new MorphBind(faceMeshes, faceMeshes[0].morphTargetDictionary[morphName]),
      );
    manager.registerExpression(expression);
  };
  for (const [emotion, suffix] of Object.entries(EMOTION_MORPH_SUFFIXES)) {
    manager.unregisterExpression(manager.getExpression(emotion));
    registerMorphExpression(emotion, [`Fcl_BRW_${suffix}`, `Fcl_EYE_${suffix}`]);
    registerMorphExpression(emotionMouthName(emotion), [`Fcl_MTH_${suffix}`]);
  }
}
