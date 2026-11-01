import { BodyPerformance, GESTURES, POSES, idleModes } from "./body-performance.js";
import {
  expressionMouthName,
  expressionNames,
  registerFaceExpressions,
  vowelShapeAt,
} from "./face-expressions.js";
import { GAZE_TARGETS, Gaze } from "./gaze.js";
import { emotionMouthTarget, followLevel } from "./renderer-controls.js";

const MOUTH_SHAPES = ["aa", "ih", "ou", "ee", "oh"];
const SHAPE_CHANGE_SECONDS = 0.06;
const BLINK_MILLISECONDS = 160;

export class AvatarPerformer {
  constructor({ vrm, morphNames, gazeTarget, gazeOrigin, createExpression }) {
    this.vrm = vrm;
    registerFaceExpressions(vrm, morphNames, createExpression);
    vrm.lookAt.target = gazeTarget;
    this.gaze = new Gaze(gazeTarget, gazeOrigin);
    this.body = new BodyPerformance((bone) =>
      vrm.humanoid.getNormalizedBoneNode(bone),
    );
    this.expression = "neutral";
    this.expressionIntensity = 0;
    this.emotionMouth = 1;
    this.restingExpression = null;
    this.speech = { startedAt: 0, vowels: [] };
    this.shapeWeights = { aa: 1, ih: 0, ou: 0, ee: 0, oh: 0 };
    this.nextBlinkTime = 3000;
  }

  setExpression(expression, intensity = 1) {
    const manager = this.vrm.expressionManager;
    manager.setValue(this.expression, 0);
    manager.setValue(expressionMouthName(this.expression), 0);
    this.expression = expression;
    this.expressionIntensity = intensity;
    manager.setValue(expression, intensity);
  }

  beginSpeech({ emotion, vowels = [] }) {
    this.restingExpression ??= {
      expression: this.expression,
      intensity: this.expressionIntensity,
    };
    this.setExpression(emotion || "neutral");
    this.speech = { startedAt: performance.now(), vowels };
  }

  endSpeech() {
    this.speech = { startedAt: 0, vowels: [] };
    if (!this.restingExpression) return;
    const { expression, intensity } = this.restingExpression;
    this.restingExpression = null;
    this.setExpression(expression, intensity);
  }

  perform(action, name) {
    const actions = {
      gesture: () => this.body.playGesture(name, performance.now()),
      pose: () => this.body.setPose(name),
      look: () => this.gaze.look(name),
      capabilities: () => ({
        expressions: expressionNames(),
        gestures: Object.keys(GESTURES),
        poses: Object.keys(POSES),
        gaze: Object.keys(GAZE_TARGETS),
        idle: idleModes(),
      }),
    };
    if (!Object.hasOwn(actions, action))
      throw new Error(`Unknown performance: ${action}`);
    return actions[action]();
  }

  updateMouth(timestamp, delta, state) {
    const manager = this.vrm.expressionManager;
    const seconds = (timestamp - this.speech.startedAt) / 1000;
    const activeShape = vowelShapeAt(this.speech.vowels, seconds);
    const share = Math.min(1, delta / SHAPE_CHANGE_SECONDS);
    for (const shape of MOUTH_SHAPES) {
      const target = shape === activeShape ? 1 : 0;
      this.shapeWeights[shape] += (target - this.shapeWeights[shape]) * share;
      manager.setValue(shape, this.shapeWeights[shape] * state.mouth);
    }
    this.emotionMouth = followLevel(
      this.emotionMouth,
      emotionMouthTarget(timestamp, state.lastVoiceTime),
      delta,
    );
    manager.setValue(
      expressionMouthName(this.expression),
      this.expressionIntensity * this.emotionMouth,
    );
  }

  updateBlink(timestamp, random = Math.random) {
    const closing = timestamp - this.nextBlinkTime;
    const closed =
      closing >= 0 && closing < BLINK_MILLISECONDS
        ? Math.sin((closing / BLINK_MILLISECONDS) * Math.PI)
        : 0;
    this.vrm.expressionManager.setValue("blink", closed);
    if (closing >= BLINK_MILLISECONDS)
      this.nextBlinkTime = timestamp + 2200 + random() * 3800;
  }

  update(timestamp, delta, state) {
    this.updateMouth(timestamp, delta, state);
    this.updateBlink(timestamp);
    this.gaze.update(timestamp, delta);
    this.body.update(timestamp, delta, {
      idleMode: state.idleMode,
      mouth: state.mouth,
      headTurn: this.gaze.headTurn(),
    });
    this.vrm.scene.position.y =
      state.idleMode === "floating" ? Math.sin(timestamp / 1500) * 0.03 : 0;
    this.vrm.update(delta);
  }
}
