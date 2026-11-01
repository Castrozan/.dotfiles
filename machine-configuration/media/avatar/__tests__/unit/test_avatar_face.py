import shutil

import pytest

from renderer_module_runner import run_renderer_module

requires_node = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is unavailable"
)

FAKE_FACE = """
const morphNames = ["Face.M_Fcl_MTH_A", "Face.M_Fcl_BRW_Joy", "Face.M_Fcl_EYE_Joy", "Face.M_Fcl_MTH_Fun"];
const face = { morphTargetInfluences: [0, 0, 0, 0] };
const expressions = {};
const manager = {
  getExpression: (name) => expressions[name] ?? null,
  unregisterExpression: (expression) => { delete expressions[expression.name]; },
  registerExpression: (expression) => { expressions[expression.name] = expression; },
};
const vrm = { scene: { traverse: (visit) => visit(face) }, expressionManager: manager };
const createExpression = (name) => ({ name, binds: [], addBind(bind) { this.binds.push(bind); } });
"""


@requires_node
def test_face_morph_names_are_read_from_the_primitive_when_the_mesh_has_none():
    result = run_renderer_module(
        "face-expressions.js",
        """
        const names = rendererModule.faceMorphNames({ meshes: [
          { primitives: [{}] },
          { primitives: [{ extras: { targetNames: ["Face.Fcl_MTH_A"] } }] },
        ] });
        console.log(JSON.stringify(names));
        """,
    )
    assert result == ["Face.Fcl_MTH_A"]


@requires_node
def test_an_expression_keeps_the_upper_face_and_leaves_the_mouth_to_speech():
    result = run_renderer_module(
        "face-expressions.js",
        FAKE_FACE
        + """
        rendererModule.registerFaceExpressions(vrm, morphNames, createExpression);
        expressions.happy.binds.forEach((bind) => bind.applyWeight(1));
        const upperFace = [...face.morphTargetInfluences];
        expressions[rendererModule.expressionMouthName("happy")].binds.forEach(
          (bind) => bind.applyWeight(0.5),
        );
        console.log(JSON.stringify({ upperFace, whole: face.morphTargetInfluences }));
        """,
    )
    assert result["upperFace"] == [0, 1, 1, 0]
    assert result["whole"] == [0, 1, 1, 0.5]


@requires_node
def test_the_mouth_forms_the_spoken_vowel_and_falls_back_to_open():
    result = run_renderer_module(
        "face-expressions.js",
        """
        const vowels = [{ shape: "oh", start: 1, end: 1.2 }];
        console.log(JSON.stringify({
          during: rendererModule.vowelShapeAt(vowels, 1.1),
          otherwise: rendererModule.vowelShapeAt(vowels, 3),
          withoutTiming: rendererModule.vowelShapeAt([], 1),
        }));
        """,
    )
    assert result == {"during": "oh", "otherwise": "aa", "withoutTiming": "aa"}
